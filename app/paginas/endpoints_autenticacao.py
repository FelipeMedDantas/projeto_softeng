"""Endpoints HTTP server-side para a sessão de autenticação."""

import json
import logging
from urllib.parse import urlencode

from reflex.utils.exec import is_prod_mode
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse, Response
from starlette.routing import Route
from starlette.types import ASGIApp, Receive, Scope, Send

from app.dados.repositorio import obter_repositorio
from app.dominio.autorizacao import (
    PERFIS_POR_ROTA,
    destino_pos_login,
    perfil_pode_acessar,
    rota_inicial,
)
from app.dominio.parametros import ler_parametros
from app.servicos.autenticacao import autenticar, encerrar_sessao, validar_sessao


NOME_COOKIE_SESSAO = "atendimento_sessao"
ROTAS_PUBLICAS = {
    "/login",
    "/403",
    "/404",
    "/favicon.ico",
    "/robots.txt",
    "/sitemap.xml",
    "/manifest.json",
}


def _resposta_json(conteudo: dict[str, object], status_code: int) -> JSONResponse:
    resposta = JSONResponse(conteudo, status_code=status_code)
    resposta.headers["Cache-Control"] = "no-store"
    resposta.headers["Pragma"] = "no-cache"
    resposta.headers["X-Content-Type-Options"] = "nosniff"
    return resposta


def _configurar_cookie_sessao(resposta: Response, token: str, max_age: int) -> None:
    resposta.set_cookie(
        key=NOME_COOKIE_SESSAO,
        value=token,
        max_age=max_age,
        path="/",
        secure=is_prod_mode(),
        httponly=True,
        samesite="strict",
    )


def _remover_cookie_sessao(resposta: Response) -> None:
    resposta.delete_cookie(
        key=NOME_COOKIE_SESSAO,
        path="/",
        secure=is_prod_mode(),
        httponly=True,
        samesite="strict",
    )


async def endpoint_login(request: Request) -> JSONResponse:
    try:
        corpo = await request.json()
    except (json.JSONDecodeError, UnicodeDecodeError):
        return _resposta_json(
            {"sucesso": False, "mensagem": "E-mail ou senha incorretos."},
            400,
        )

    if not isinstance(corpo, dict):
        corpo = {}
    email = corpo.get("email")
    senha = corpo.get("senha")
    candidato = corpo.get("next")
    try:
        resultado = autenticar(
            email if isinstance(email, str) else "",
            senha if isinstance(senha, str) else "",
            repositorio=obter_repositorio(),
        )
    except Exception:
        logging.exception("Erro inesperado ao processar login.")
        return _resposta_json(
            {
                "sucesso": False,
                "mensagem": "Ocorreu um erro interno ao autenticar.",
            },
            500,
        )
    perfil = resultado.perfil.value if resultado.perfil is not None else None
    destino = (
        destino_pos_login(candidato, resultado.perfil)
        if resultado.sucesso and resultado.perfil is not None
        else None
    )
    status_code = 200 if resultado.sucesso else 401
    resposta = _resposta_json(
        {
            "sucesso": resultado.sucesso,
            "mensagem": resultado.mensagem,
            "usuario_id": resultado.usuario_id,
            "perfil": perfil,
            "destino": destino,
        },
        status_code,
    )
    if resultado.sucesso and resultado.token_sessao:
        tempo_sessao = ler_parametros(obter_repositorio()).tempo_sessao_min
        _configurar_cookie_sessao(
            resposta,
            resultado.token_sessao,
            max_age=tempo_sessao * 60,
        )
    return resposta


async def endpoint_sessao(request: Request) -> JSONResponse:
    token = request.cookies.get(NOME_COOKIE_SESSAO)
    repositorio = obter_repositorio()
    resultado = validar_sessao(token, repositorio=repositorio)
    perfil = resultado.perfil.value if resultado.perfil is not None else None
    resposta = _resposta_json(
        {
            "sucesso": resultado.sucesso,
            "mensagem": resultado.mensagem,
            "usuario_id": resultado.usuario_id,
            "perfil": perfil,
        },
        200,
    )
    if resultado.sucesso and token:
        tempo_sessao = ler_parametros(repositorio).tempo_sessao_min
        _configurar_cookie_sessao(resposta, token, max_age=tempo_sessao * 60)
    elif token:
        _remover_cookie_sessao(resposta)
    return resposta


async def endpoint_logout(request: Request) -> JSONResponse:
    token = request.cookies.get(NOME_COOKIE_SESSAO)
    resultado = encerrar_sessao(token, repositorio=obter_repositorio())
    resposta = _resposta_json(
        {"sucesso": resultado.sucesso, "mensagem": resultado.mensagem},
        200,
    )
    _remover_cookie_sessao(resposta)
    return resposta


def proteger_paginas(aplicacao: ASGIApp) -> ASGIApp:
    """Valida sessão e perfil antes de entregar uma rota protegida."""

    async def middleware(scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and scope["method"] in {"GET", "HEAD"}:
            caminho = scope.get("path", "/")
            rota = caminho.rstrip("/") or "/"
            arquivo_estatico = caminho.lower().endswith(
                (".css", ".js", ".map", ".ico", ".png", ".jpg", ".jpeg", ".svg", ".woff", ".woff2", ".ttf")
            )
            publico = (
                rota in ROTAS_PUBLICAS
                or caminho.startswith(("/api/", "/_", "/assets/", "/static/"))
                or arquivo_estatico
            )
            if not publico and rota not in PERFIS_POR_ROTA and rota != "/":
                resposta = RedirectResponse("/404", status_code=303)
                await resposta(scope, receive, send)
                return

            if not publico:
                requisicao = Request(scope, receive)
                token = requisicao.cookies.get(NOME_COOKIE_SESSAO)
                resultado = validar_sessao(
                    token,
                    repositorio=obter_repositorio(),
                )
                if not resultado.sucesso or resultado.perfil is None:
                    parametros: dict[str, str] = {}
                    if resultado.mensagem == "Sua sessão expirou. Entre novamente.":
                        parametros["sessao"] = "expirada"
                    if rota != "/":
                        parametros["next"] = rota
                    destino = "/login"
                    if parametros:
                        destino = f"{destino}?{urlencode(parametros)}"
                    resposta = RedirectResponse(destino, status_code=303)
                    if token:
                        _remover_cookie_sessao(resposta)
                    await resposta(scope, receive, send)
                    return

                if rota == "/":
                    resposta = RedirectResponse(
                        rota_inicial(resultado.perfil),
                        status_code=303,
                    )
                    await resposta(scope, receive, send)
                    return

                if not perfil_pode_acessar(resultado.perfil, rota):
                    resposta = RedirectResponse("/403", status_code=303)
                    await resposta(scope, receive, send)
                    return

        await aplicacao(scope, receive, send)

    return middleware


rotas_autenticacao = Starlette(
    routes=[
        Route("/api/autenticacao/login", endpoint_login, methods=["POST"]),
        Route("/api/autenticacao/sessao", endpoint_sessao, methods=["GET"]),
        Route("/api/autenticacao/logout", endpoint_logout, methods=["POST"]),
    ]
)