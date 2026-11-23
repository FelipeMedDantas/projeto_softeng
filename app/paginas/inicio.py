"""Página inicial do Sistema de Priorização de Atendimento."""

import reflex as rx

from app.componentes.faixa_cor import faixa_cor
from app.componentes.layout import layout_base
from app.componentes.mensagens import mensagem


def index() -> rx.Component:
    """Apresenta a página inicial fictícia do sistema."""

    return layout_base(
        rx.vstack(
            rx.heading("Visão geral", color="#183b32", size="6"),
            mensagem("Ambiente de demonstração. Todos os dados são fictícios."),
            rx.vstack(
                rx.heading("Faixa ilustrativa", color="#183b32", size="3"),
                faixa_cor(8),
                align_items="start",
                spacing="3",
                width="100%",
            ),
            align_items="stretch",
            spacing="5",
            width="100%",
        ),
    )