"""Aplicação Reflex do Sistema de Priorização de Atendimento."""

import reflex as rx

from app.dados.repositorio import obter_repositorio
from app.componentes.layout import EstadoLayout
from app.paginas.inicio import index
from app.paginas.endpoints_autenticacao import proteger_paginas, rotas_autenticacao
from app.paginas.login import EstadoLogin, login


obter_repositorio()

app = rx.App(
	html_lang="pt-BR",
	stylesheets=["/login.css"],
	api_transformer=[rotas_autenticacao, proteger_paginas],
)
app.add_page(
	index,
	route="/",
	title="Sistema de Priorização de Atendimento",
	on_load=EstadoLayout.verificar_sessao,
)
app.add_page(
	login,
	route="/login",
	title="Entrar na equipe",
	on_load=EstadoLogin.verificar_sessao,
)
