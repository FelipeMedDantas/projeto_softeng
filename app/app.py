"""Aplicação Reflex do Sistema de Priorização de Atendimento."""

import reflex as rx

from app.dados.repositorio import inicializar_repositorio
from app.componentes.layout import EstadoLayout
from app.paginas.inicio import index
from app.paginas.endpoints_autenticacao import proteger_paginas, rotas_autenticacao
from app.paginas.login import EstadoLogin, login
from app.paginas.perfis import (
	PAGINAS_PROTEGIDAS,
	acesso_negado,
	nao_encontrada,
)


inicializar_repositorio()

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
for rota, (pagina, titulo) in PAGINAS_PROTEGIDAS.items():
	app.add_page(
		pagina,
		route=rota,
		title=titulo,
		on_load=EstadoLayout.verificar_sessao,
	)
app.add_page(acesso_negado, route="/403", title="Acesso negado")
app.add_page(nao_encontrada, route="/404", title="Página não encontrada")
