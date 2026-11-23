"""Primitivas Python puras para autenticação da equipe."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import hmac
from math import ceil
import secrets
from typing import TYPE_CHECKING

from app.dominio.modelos import PerfilUsuario, SessaoAutenticada, Usuario
from app.dominio.parametros import ler_parametros

if TYPE_CHECKING:
    from app.dados.repositorio import RepositorioMemoria


_ALGORITMO_HASH = "pbkdf2_sha256"
_TAMANHO_SALT_BYTES = 16
_TAMANHO_HASH_BYTES = 32
_SALT_USUARIO_INEXISTENTE = secrets.token_bytes(_TAMANHO_SALT_BYTES)
_PERFIS_EQUIPE = {
    PerfilUsuario.ADMIN,
    PerfilUsuario.RECEPCAO,
    PerfilUsuario.MEDICO,
}


@dataclass(frozen=True)
class ResultadoAutenticacao:
    """Resultado de login sem expor o token em representações ou logs."""

    sucesso: bool
    mensagem: str
    usuario_id: str | None = None
    perfil: PerfilUsuario | None = None
    token_sessao: str | None = field(default=None, repr=False, compare=False)


def criar_hash_senha(senha: str) -> str:
    """Deriva um hash PBKDF2 com salt aleatório e custo configurado."""

    if not isinstance(senha, str) or not senha:
        raise ValueError("A senha não pode estar vazia.")

    iteracoes = ler_parametros().iteracoes_hash_senha
    salt = secrets.token_bytes(_TAMANHO_SALT_BYTES)
    derivado = hashlib.pbkdf2_hmac(
        "sha256",
        senha.encode("utf-8"),
        salt,
        iteracoes,
        dklen=_TAMANHO_HASH_BYTES,
    )
    return f"{_ALGORITMO_HASH}${iteracoes}${salt.hex()}${derivado.hex()}"


def verificar_senha(senha: str, senha_hash: str) -> bool:
    """Verifica uma senha sem revelar detalhes do hash armazenado."""

    if not isinstance(senha, str) or not isinstance(senha_hash, str):
        return False

    try:
        algoritmo, iteracoes_texto, salt_hexadecimal, hash_hexadecimal = senha_hash.split("$")
        iteracoes = int(iteracoes_texto)
        salt = bytes.fromhex(salt_hexadecimal)
        hash_esperado = bytes.fromhex(hash_hexadecimal)
    except (ValueError, TypeError):
        return False

    if (
        algoritmo != _ALGORITMO_HASH
        or iteracoes <= 0
        or len(salt) != _TAMANHO_SALT_BYTES
        or len(hash_esperado) != _TAMANHO_HASH_BYTES
    ):
        return False

    hash_calculado = hashlib.pbkdf2_hmac(
        "sha256",
        senha.encode("utf-8"),
        salt,
        iteracoes,
        dklen=_TAMANHO_HASH_BYTES,
    )
    return hmac.compare_digest(hash_calculado, hash_esperado)


def _agora_utc(agora: datetime | None) -> datetime:
    instante = agora or datetime.now(timezone.utc)
    if instante.tzinfo is None:
        return instante.replace(tzinfo=timezone.utc)
    return instante.astimezone(timezone.utc)


def _normalizar_email(email: str) -> str:
    return email.strip().lower() if isinstance(email, str) else ""


def _verificar_senha_sem_conta(senha: str, iteracoes: int) -> None:
    """Executa o custo de hash configurado sem armazenar dados da tentativa."""

    derivado = hashlib.pbkdf2_hmac(
        "sha256",
        senha.encode("utf-8") if isinstance(senha, str) else b"",
        _SALT_USUARIO_INEXISTENTE,
        iteracoes,
        dklen=_TAMANHO_HASH_BYTES,
    )
    hmac.compare_digest(derivado, bytes(_TAMANHO_HASH_BYTES))


def _mensagem_bloqueio(bloqueado_ate: datetime, agora: datetime) -> str:
    minutos_restantes = max(1, ceil((bloqueado_ate - agora).total_seconds() / 60))
    unidade = "minuto" if minutos_restantes == 1 else "minutos"
    return f"Acesso bloqueado. Tente novamente em {minutos_restantes} {unidade}."


def autenticar(
    email: str,
    senha: str,
    *,
    agora: datetime | None = None,
    repositorio: "RepositorioMemoria | None" = None,
) -> ResultadoAutenticacao:
    """Autentica um perfil de equipe e cria sessão opaca no repositório."""

    if repositorio is None:
        from app.dados.repositorio import obter_repositorio

        repositorio = obter_repositorio()

    instante = _agora_utc(agora)
    parametros = ler_parametros(repositorio)
    email_normalizado = _normalizar_email(email)
    tentativa = repositorio.obter_tentativa_login(email_normalizado, instante)
    if tentativa is not None and tentativa.bloqueado_ate is not None:
        repositorio.registrar_evento_autenticacao("login_bloqueado", None, instante)
        return ResultadoAutenticacao(
            False,
            _mensagem_bloqueio(tentativa.bloqueado_ate, instante),
        )

    usuario = next(
        (
            registro
            for registro in repositorio.listar("usuarios")
            if isinstance(registro, Usuario) and registro.email == email_normalizado
        ),
        None,
    )
    senha_valida = (
        verificar_senha(senha, usuario.senha_hash)
        if usuario is not None
        else False
    )
    if usuario is None:
        _verificar_senha_sem_conta(senha, parametros.iteracoes_hash_senha)

    if (
        usuario is None
        or not senha_valida
        or usuario.perfil not in _PERFIS_EQUIPE
    ):
        estado_tentativas = repositorio.registrar_falha_login(
            email_normalizado,
            instante,
            parametros.max_tentativas_login,
            parametros.tempo_bloqueio_min,
        )
        bloqueado = estado_tentativas.bloqueado_ate is not None
        repositorio.registrar_evento_autenticacao(
            "login_bloqueado" if bloqueado else "login_falhou",
            usuario.id if usuario is not None else None,
            instante,
        )
        mensagem = (
            _mensagem_bloqueio(estado_tentativas.bloqueado_ate, instante)
            if estado_tentativas.bloqueado_ate is not None
            else "E-mail ou senha incorretos."
        )
        return ResultadoAutenticacao(False, mensagem)

    if not usuario.ativo:
        repositorio.limpar_tentativas_login(email_normalizado)
        repositorio.registrar_evento_autenticacao("login_falhou", usuario.id, instante)
        return ResultadoAutenticacao(
            False,
            "Conta desativada. Procure a administração.",
        )

    repositorio.limpar_tentativas_login(email_normalizado)
    token_sessao = secrets.token_urlsafe(32)
    digest_token = hashlib.sha256(token_sessao.encode("utf-8")).hexdigest()
    repositorio.criar_sessao(
        SessaoAutenticada(
            id=digest_token,
            usuario_id=usuario.id,
            criada_em=instante,
            ultima_atividade=instante,
        )
    )
    repositorio.registrar_evento_autenticacao("login_sucesso", usuario.id, instante)
    return ResultadoAutenticacao(
        True,
        "Login realizado com sucesso.",
        usuario_id=usuario.id,
        perfil=usuario.perfil,
        token_sessao=token_sessao,
    )


def validar_sessao(
    token_sessao: str | None,
    *,
    agora: datetime | None = None,
    repositorio: "RepositorioMemoria | None" = None,
) -> ResultadoAutenticacao:
    """Valida e renova atividade de uma sessão sem expor o digest."""

    if repositorio is None:
        from app.dados.repositorio import obter_repositorio

        repositorio = obter_repositorio()

    if not token_sessao:
        return ResultadoAutenticacao(False, "Entre para continuar.")

    instante = _agora_utc(agora)
    parametros = ler_parametros(repositorio)
    digest_token = hashlib.sha256(token_sessao.encode("utf-8")).hexdigest()
    sessao, expirou = repositorio.renovar_sessao(
        digest_token,
        instante,
        parametros.tempo_sessao_min,
    )
    if sessao is None:
        mensagem = (
            "Sua sessão expirou. Entre novamente."
            if expirou
            else "Entre para continuar."
        )
        return ResultadoAutenticacao(False, mensagem)

    usuario = repositorio.obter("usuarios", sessao.usuario_id)
    if (
        not isinstance(usuario, Usuario)
        or not usuario.ativo
        or usuario.perfil not in _PERFIS_EQUIPE
    ):
        repositorio.invalidar_sessao(digest_token)
        return ResultadoAutenticacao(
            False,
            "Sua sessão não está mais ativa. Entre novamente.",
        )

    return ResultadoAutenticacao(
        True,
        "Sessão ativa.",
        usuario_id=usuario.id,
        perfil=usuario.perfil,
    )


def encerrar_sessao(
    token_sessao: str | None,
    *,
    agora: datetime | None = None,
    repositorio: "RepositorioMemoria | None" = None,
) -> ResultadoAutenticacao:
    """Invalida uma sessão e audita logout sem guardar o token."""

    if repositorio is None:
        from app.dados.repositorio import obter_repositorio

        repositorio = obter_repositorio()

    instante = _agora_utc(agora)
    if token_sessao:
        digest_token = hashlib.sha256(token_sessao.encode("utf-8")).hexdigest()
        sessao = repositorio.invalidar_sessao(digest_token)
        if sessao is not None:
            repositorio.registrar_evento_autenticacao(
                "logout",
                sessao.usuario_id,
                instante,
            )
    return ResultadoAutenticacao(True, "Sessão encerrada.")