"""Testes de registro das páginas por perfil."""

import pytest
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from app.app import app
from app.dados.repositorio import RepositorioMemoria
from app.dominio.autorizacao import PERFIS_POR_ROTA, perfil_pode_acessar
from app.dominio.modelos import PerfilUsuario
from app.componentes.layout import links_navegacao_perfil
from app.paginas.perfis import PAGINAS_PROTEGIDAS
from app.servicos.autenticacao import ResultadoAutenticacao


def test_paginas_protegidas_correspondem_a_matriz_de_perfis() -> None:
    assert set(PAGINAS_PROTEGIDAS) == set(PERFIS_POR_ROTA)


def test_aplicacao_registra_rotas_de_perfil_e_paginas_de_erro() -> None:
    rotas_registradas = {
        "/" if pagina.route == "index" else f"/{pagina.route.lstrip('/')}"
        for pagina in app._unevaluated_pages.values()
    }

    assert set(PERFIS_POR_ROTA) | {"/403", "/404"} <= rotas_registradas


def test_navegacao_apresenta_somente_links_autorizados() -> None:
    rotas_por_perfil = {
        PerfilUsuario.RECEPCAO: {"/recepcao", "/perfil"},
        PerfilUsuario.MEDICO: {"/medico", "/perfil"},
        PerfilUsuario.PACIENTE: {"/paciente"},
        PerfilUsuario.ADMIN: {"/admin", "/perfil"},
    }

    for perfil, rotas_esperadas in rotas_por_perfil.items():
        links = links_navegacao_perfil(perfil.value)
        assert {link["rota"] for link in links} == rotas_esperadas
        assert all(link["rotulo"] for link in links)


def test_navegacao_nao_apresenta_links_para_perfil_desconhecido() -> None:
    assert links_navegacao_perfil("desconhecido") == []


def test_guard_integrada_aplica_matriz_e_respostas_de_erro(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import app.paginas.endpoints_autenticacao as endpoints

    repositorio = RepositorioMemoria()
    monkeypatch.setattr(endpoints, "obter_repositorio", lambda: repositorio)

    async def pagina_requisitada(requisicao: Request) -> PlainTextResponse:
        return PlainTextResponse(f"pagina:{requisicao.url.path}")

    async def pagina_login(_: Request) -> PlainTextResponse:
        return PlainTextResponse("login")

    async def pagina_403(_: Request) -> PlainTextResponse:
        return PlainTextResponse("acesso negado")

    async def pagina_404(_: Request) -> PlainTextResponse:
        return PlainTextResponse("pagina nao encontrada")

    aplicacao = Starlette(
        routes=[
            *(Route(rota, pagina_requisitada) for rota in PERFIS_POR_ROTA),
            Route("/login", pagina_login),
            Route("/403", pagina_403),
            Route("/404", pagina_404),
        ]
    )
    cliente = TestClient(endpoints.proteger_paginas(aplicacao))

    for perfil in PerfilUsuario:
        resultado = ResultadoAutenticacao(
            True,
            "Sessão ativa.",
            usuario_id=f"usuario-{perfil.value}",
            perfil=perfil,
        )
        monkeypatch.setattr(
            endpoints,
            "validar_sessao",
            lambda token, *, repositorio, resultado=resultado: resultado,
        )

        for rota in PERFIS_POR_ROTA:
            resposta = cliente.get(rota, follow_redirects=False)
            if perfil_pode_acessar(perfil, rota):
                assert resposta.status_code == 200
                assert resposta.text == f"pagina:{rota}"
            else:
                assert resposta.status_code == 303
                assert resposta.headers["location"] == "/403"
                assert "pagina:" not in resposta.text

    monkeypatch.setattr(
        endpoints,
        "validar_sessao",
        lambda token, *, repositorio: ResultadoAutenticacao(
            False,
            "Entre para continuar.",
        ),
    )
    visitante = cliente.get("/recepcao", follow_redirects=False)
    assert visitante.status_code == 303
    assert visitante.headers["location"] == "/login?next=%2Frecepcao"

    inexistente = cliente.get("/rota-inexistente", follow_redirects=False)
    assert inexistente.status_code == 303
    assert inexistente.headers["location"] == "/404"
    assert cliente.get("/403").text == "acesso negado"
    assert cliente.get("/404").text == "pagina nao encontrada"