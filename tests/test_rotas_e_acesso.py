"""Testes de autorização por perfil durante o carregamento das páginas."""

import pytest

from app.app import app
from app.componentes.layout import (
    acesso_confirmado_para_rota,
    decidir_redirecionamento_guardia,
)
from app.dominio.autorizacao import PERFIS_POR_ROTA
from app.dominio.modelos import PerfilUsuario


@pytest.mark.parametrize(
    ("perfil", "rota", "rota_verificada"),
    [
        (PerfilUsuario.RECEPCAO, "/admin", "/recepcao"),
        (PerfilUsuario.ADMIN, "/recepcao", "/admin"),
    ],
)
def test_perfil_sem_permissao_redireciona_para_403_e_oculta_conteudo(
    perfil: PerfilUsuario,
    rota: str,
    rota_verificada: str,
) -> None:
    destino = decidir_redirecionamento_guardia(
        True,
        perfil,
        rota,
        "Sessão ativa.",
    )

    assert destino == "/403"
    assert not acesso_confirmado_para_rota(perfil.value, rota, rota_verificada)


def test_perfil_autorizado_mantem_rota_atual() -> None:
    assert decidir_redirecionamento_guardia(
        True,
        PerfilUsuario.RECEPCAO,
        "/recepcao",
        "Sessão ativa.",
    ) is None
    assert acesso_confirmado_para_rota(
        PerfilUsuario.RECEPCAO.value,
        "/recepcao/",
        "/recepcao",
    )


@pytest.mark.parametrize("rota", ["/admin", "/medico", "/recepcao", "/paciente", "/perfil"])
def test_todas_as_rotas_protegidas_registram_guarda_no_on_load(rota: str) -> None:
    pagina = next(
        pagina
        for pagina in app._unevaluated_pages.values()
        if f"/{pagina.route.lstrip('/')}" == rota
    )

    assert pagina.on_load is not None
    assert pagina.on_load.fn.__name__ == "verificar_sessao"


def test_sessao_ausente_preserva_rota_candidata_no_login() -> None:
    assert decidir_redirecionamento_guardia(
        False,
        None,
        "/admin",
        "Entre para continuar.",
    ) == "/login?next=%2Fadmin"


def test_matriz_central_define_as_rotas_protegidas() -> None:
    assert set(PERFIS_POR_ROTA) == {
        "/recepcao",
        "/medico",
        "/paciente",
        "/admin",
        "/perfil",
    }