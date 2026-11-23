"""Repositório único em memória para dados compartilhados entre sessões."""

from copy import deepcopy
from datetime import datetime, timedelta
import re
from threading import RLock
from typing import Callable, TypeVar, cast
from uuid import uuid4

from app.dominio.modelos import RegistroAuditoria, SessaoAutenticada, TentativaLogin


T = TypeVar("T")


class RepositorioMemoria:
    """Coordena CRUD, configuração e reset com proteção contra concorrência."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._colecoes: dict[str, dict[str, object]] = {}
        self._configuracoes: dict[str, object] = {}

    def criar(
        self,
        colecao: str,
        registro: T,
        identificador: str | None = None,
    ) -> T:
        """Insere um registro novo e rejeita identificadores duplicados."""

        chave = identificador or getattr(registro, "id", None)
        if not isinstance(chave, str) or not chave:
            raise ValueError("O registro precisa de um identificador textual.")

        with self._lock:
            registros = self._colecoes.setdefault(colecao, {})
            if chave in registros:
                raise ValueError(f"Já existe um registro com o identificador {chave}.")
            self._validar_email_unico(colecao, registros, registro)
            registros[chave] = deepcopy(registro)
            return cast(T, deepcopy(registros[chave]))

    def obter(self, colecao: str, identificador: str) -> object | None:
        """Devolve uma cópia do registro ou None quando ele não existe."""

        with self._lock:
            registro = self._colecoes.get(colecao, {}).get(identificador)
            return deepcopy(registro) if registro is not None else None

    def listar(self, colecao: str) -> list[object]:
        """Devolve cópias dos registros de uma coleção."""

        with self._lock:
            return deepcopy(list(self._colecoes.get(colecao, {}).values()))

    def atualizar(
        self,
        colecao: str,
        identificador: str,
        registro: T,
    ) -> T:
        """Substitui um registro existente sem expor referências mutáveis."""

        with self._lock:
            registros = self._colecoes.get(colecao, {})
            if identificador not in registros:
                raise ValueError(f"Não existe registro com o identificador {identificador}.")
            chave_registro = getattr(registro, "id", identificador)
            if chave_registro != identificador:
                raise ValueError("O identificador do registro não pode ser alterado.")
            self._validar_email_unico(
                colecao,
                registros,
                registro,
                ignorar_identificador=identificador,
            )
            registros[identificador] = deepcopy(registro)
            return cast(T, deepcopy(registros[identificador]))

    @staticmethod
    def _validar_email_unico(
        colecao: str,
        registros: dict[str, object],
        registro: object,
        ignorar_identificador: str | None = None,
    ) -> None:
        if colecao != "usuarios":
            return

        email = getattr(registro, "email", "")
        if not isinstance(email, str) or not email:
            return

        email_normalizado = email.strip().lower()
        for identificador, existente in registros.items():
            if identificador == ignorar_identificador:
                continue
            email_existente = getattr(existente, "email", "")
            if isinstance(email_existente, str) and email_existente.strip().lower() == email_normalizado:
                raise ValueError("Já existe um usuário com esse e-mail.")

    def remover(self, colecao: str, identificador: str) -> bool:
        """Remove um registro e informa se ele existia."""

        with self._lock:
            registros = self._colecoes.get(colecao, {})
            return registros.pop(identificador, None) is not None

    def obter_tentativa_login(
        self,
        email_normalizado: str,
        agora: datetime,
    ) -> TentativaLogin | None:
        """Lê tentativas e limpa bloqueios já encerrados atomicamente."""

        with self._lock:
            tentativas = self._colecoes.get("tentativas_login", {})
            tentativa = cast(TentativaLogin | None, tentativas.get(email_normalizado))
            if tentativa is not None and tentativa.bloqueado_ate is not None:
                if agora >= tentativa.bloqueado_ate:
                    del tentativas[email_normalizado]
                    return None
            return deepcopy(tentativa)

    def registrar_falha_login(
        self,
        email_normalizado: str,
        agora: datetime,
        max_tentativas: int,
        tempo_bloqueio_min: int,
    ) -> TentativaLogin:
        """Incrementa falhas e estabelece bloqueio sob um único lock."""

        if max_tentativas <= 0 or tempo_bloqueio_min <= 0:
            raise ValueError("Os limites de tentativas e bloqueio devem ser maiores que zero.")

        with self._lock:
            tentativas = self._colecoes.setdefault("tentativas_login", {})
            atual = cast(TentativaLogin | None, tentativas.get(email_normalizado))
            if atual is not None and atual.bloqueado_ate is not None:
                if agora < atual.bloqueado_ate:
                    return cast(TentativaLogin, deepcopy(atual))
                atual = None

            falhas = (atual.falhas_consecutivas if atual is not None else 0) + 1
            bloqueado_ate = (
                agora + timedelta(minutes=tempo_bloqueio_min)
                if falhas >= max_tentativas
                else None
            )
            resultado = TentativaLogin(
                id=email_normalizado,
                falhas_consecutivas=falhas,
                bloqueado_ate=bloqueado_ate,
            )
            tentativas[email_normalizado] = deepcopy(resultado)
            return deepcopy(resultado)

    def limpar_tentativas_login(self, email_normalizado: str) -> bool:
        """Zera o estado de falhas após autenticação válida."""

        with self._lock:
            tentativas = self._colecoes.get("tentativas_login", {})
            return tentativas.pop(email_normalizado, None) is not None

    def criar_sessao(self, sessao: SessaoAutenticada) -> SessaoAutenticada:
        """Armazena uma sessão indexada pelo digest opaco do token."""

        with self._lock:
            sessoes = self._colecoes.setdefault("sessoes", {})
            if sessao.id in sessoes:
                raise ValueError("Já existe uma sessão com esse identificador.")
            sessoes[sessao.id] = deepcopy(sessao)
            return cast(SessaoAutenticada, deepcopy(sessoes[sessao.id]))

    def renovar_sessao(
        self,
        digest_token: str,
        agora: datetime,
        tempo_sessao_min: int,
    ) -> tuple[SessaoAutenticada | None, bool]:
        """Valida e renova atividade, ou remove sessão expirada atomicamente."""

        if tempo_sessao_min <= 0:
            raise ValueError("O tempo de sessão deve ser maior que zero.")

        with self._lock:
            sessoes = self._colecoes.get("sessoes", {})
            sessao = cast(SessaoAutenticada | None, sessoes.get(digest_token))
            if sessao is None:
                return None, False

            if agora - sessao.ultima_atividade >= timedelta(minutes=tempo_sessao_min):
                del sessoes[digest_token]
                return None, True

            sessao_atualizada = deepcopy(sessao)
            sessao_atualizada.ultima_atividade = agora
            sessoes[digest_token] = sessao_atualizada
            return deepcopy(sessao_atualizada), False

    def invalidar_sessao(self, digest_token: str) -> SessaoAutenticada | None:
        """Remove e devolve a sessão para impedir sua reutilização."""

        with self._lock:
            sessoes = self._colecoes.get("sessoes", {})
            sessao = sessoes.pop(digest_token, None)
            return cast(SessaoAutenticada | None, deepcopy(sessao))

    def registrar_evento_autenticacao(
        self,
        acao: str,
        usuario_id: str | None,
        agora: datetime,
    ) -> RegistroAuditoria:
        """Audita somente categorias permitidas e identificadores internos."""

        acoes_permitidas = {
            "login_sucesso",
            "login_falhou",
            "login_bloqueado",
            "logout",
        }
        if acao not in acoes_permitidas:
            raise ValueError("A ação de autenticação não é permitida na auditoria.")

        registro = RegistroAuditoria(
            id=f"auditoria-{uuid4().hex}",
            usuario_id=usuario_id,
            acao=acao,
            entidade="Autenticacao",
            entidade_id=usuario_id or "",
            criado_em=agora,
        )
        return self.criar("auditoria", registro)

    def registrar_evento_acesso_negado(
        self,
        usuario_id: str | None,
        operacao: str,
        agora: datetime,
    ) -> RegistroAuditoria:
        """Audita uma operação negada sem aceitar dados livres como identificador."""

        if not isinstance(operacao, str) or re.fullmatch(r"[a-z][a-z0-9_]{0,63}", operacao) is None:
            raise ValueError("A operação de autorização deve ser um identificador técnico válido.")

        registro = RegistroAuditoria(
            id=f"auditoria-{uuid4().hex}",
            usuario_id=usuario_id,
            acao="acesso_negado",
            entidade="Operacao",
            entidade_id=operacao,
            criado_em=agora,
        )
        return self.criar("auditoria", registro)

    def obter_configuracao(self, chave: str, padrao: T) -> T:
        """Lê uma configuração protegida pelo mesmo lock do repositório."""

        with self._lock:
            valor = self._configuracoes.get(chave, padrao)
            return cast(T, deepcopy(valor))

    def salvar_configuracao(self, chave: str, valor: object) -> None:
        """Salva uma configuração compartilhada sob o lock."""

        with self._lock:
            self._configuracoes[chave] = deepcopy(valor)

    def atualizar_configuracao(
        self,
        chave: str,
        padrao: T,
        transformacao: Callable[[T], T],
    ) -> T:
        """Lê, valida e grava uma configuração em uma única transação."""

        with self._lock:
            atual = cast(T, deepcopy(self._configuracoes.get(chave, padrao)))
            atualizado = transformacao(atual)
            self._configuracoes[chave] = deepcopy(atualizado)
            return cast(T, deepcopy(atualizado))

    def restaurar_estado_inicial(self) -> None:
        """Limpa as coleções e reconstroi o estado definido pelo seed."""

        with self._lock:
            self._colecoes.clear()
            self._configuracoes.clear()
            from app.dados.seed import carregar_seed

            carregar_seed(self)


_repositorio = RepositorioMemoria()
_bloqueio_inicializacao_seed = RLock()
_seed_carregado = False


def inicializar_repositorio() -> RepositorioMemoria:
    """Carrega o seed uma vez e devolve o repositório compartilhado."""

    global _seed_carregado
    with _bloqueio_inicializacao_seed:
        if not _seed_carregado:
            _seed_carregado = True
            try:
                from app.dados.seed import carregar_seed

                carregar_seed(_repositorio)
            except Exception:
                _seed_carregado = False
                raise
    return _repositorio


def obter_repositorio() -> RepositorioMemoria:
    """Devolve o repositório compartilhado depois de garantir o seed."""

    return inicializar_repositorio()


inicializar_repositorio()