"""Testes da política de rotas e acesso por perfil."""

import pytest

from app.dados.repositorio import RepositorioMemoria
from app.dominio.autorizacao import (
    destino_pos_login,
    perfil_pode_acessar,
    rota_inicial,
    rotas_autorizadas,
)
from app.dominio.modelos import PerfilUsuario, Usuario
from app.servicos.autorizacao import exigir_perfil_para_operacao


@pytest.mark.parametrize(
    ("perfil", "rota_esperada"),
    [
        (PerfilUsuario.RECEPCAO, "/recepcao"),
        (PerfilUsuario.MEDICO, "/medico"),
        (PerfilUsuario.PACIENTE, "/paciente"),
        (PerfilUsuario.ADMIN, "/admin"),
    ],
)
def test_rota_inicial_corresponde_ao_perfil(
    perfil: PerfilUsuario,
    rota_esperada: str,
) -> None:
    assert rota_inicial(perfil) == rota_esperada
    assert perfil_pode_acessar(perfil, rota_esperada)


@pytest.mark.parametrize(
    ("perfil", "rotas_esperadas"),
    [
        (PerfilUsuario.RECEPCAO, {"/recepcao", "/perfil"}),
        (PerfilUsuario.MEDICO, {"/medico", "/perfil"}),
        (PerfilUsuario.PACIENTE, {"/paciente"}),
        (PerfilUsuario.ADMIN, {"/admin", "/perfil"}),
    ],
)
def test_perfil_recebe_exatamente_suas_rotas(
    perfil: PerfilUsuario,
    rotas_esperadas: set[str],
) -> None:
    assert set(rotas_autorizadas(perfil)) == rotas_esperadas
    assert all(perfil_pode_acessar(perfil, rota) for rota in rotas_esperadas)


@pytest.mark.parametrize("perfil", list(PerfilUsuario))
def test_perfil_nao_acessa_rota_de_outro_perfil(perfil: PerfilUsuario) -> None:
    assert not perfil_pode_acessar(perfil, "/rota-inexistente")
    assert not perfil_pode_acessar(perfil, "/login")


@pytest.mark.parametrize(
    ("candidato", "destino_esperado"),
    [
        ("/perfil", "/perfil"),
        ("/admin?aba=usuarios", "/admin?aba=usuarios"),
        ("/admin/", "/admin"),
        ("https://externo.example/admin", "/admin"),
        ("//externo.example/admin", "/admin"),
        ("///externo.example/admin", "/admin"),
        ("javascript:alert(1)", "/admin"),
        ("/admin\\@externo.example", "/admin"),
        ("/admin#fragmento", "/admin"),
        ("/recepcao", "/admin"),
        ("/nao-existe", "/admin"),
        ("caminho-relativo", "/admin"),
        (None, "/admin"),
    ],
)
def test_destino_pos_login_aceita_somente_rota_local_autorizada(
    candidato: str | None,
    destino_esperado: str,
) -> None:
    assert destino_pos_login(candidato, PerfilUsuario.ADMIN) == destino_esperado


def test_operacao_de_servico_negada_nao_muta_estado_e_audita_sem_segredos() -> None:
    from datetime import datetime, timezone

    repositorio = RepositorioMemoria()
    usuario = Usuario(
        "usuario-recepcao",
        "Pessoa Fictícia",
        PerfilUsuario.RECEPCAO,
        senha_hash="hash-secreto-ficticio",
    )
    agora = datetime(2026, 11, 23, 12, 0, tzinfo=timezone.utc)

    def alterar_configuracao() -> None:
        exigir_perfil_para_operacao(
            usuario,
            {PerfilUsuario.ADMIN},
            "alterar_parametros",
            agora=agora,
            repositorio=repositorio,
        )
        repositorio.salvar_configuracao("limite", 10)

    with pytest.raises(PermissionError, match="não tem permissão"):
        alterar_configuracao()

    assert repositorio.obter_configuracao("limite", None) is None
    registros = repositorio.listar("auditoria")
    assert len(registros) == 1
    assert registros[0].usuario_id == usuario.id
    assert registros[0].acao == "acesso_negado"
    assert registros[0].entidade_id == "alterar_parametros"
    assert registros[0].criado_em == agora
    assert "hash-secreto-ficticio" not in repr(registros[0])


def test_operacao_de_servico_autorizada_nao_registra_negacao() -> None:
    repositorio = RepositorioMemoria()
    usuario = Usuario("usuario-admin", "Admin Fictício", PerfilUsuario.ADMIN)

    exigir_perfil_para_operacao(
        usuario,
        {PerfilUsuario.ADMIN},
        "alterar_parametros",
        repositorio=repositorio,
    )

    assert repositorio.listar("auditoria") == []