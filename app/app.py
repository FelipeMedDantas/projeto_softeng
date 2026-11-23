"""Aplicação Reflex do Sistema de Priorização de Atendimento."""

import reflex as rx

from app.dados.seed import carregar_seed
from app.paginas.inicio import index


carregar_seed()

app = rx.App(html_lang="pt-BR")
app.add_page(index, route="/", title="Sistema de Priorização de Atendimento")
