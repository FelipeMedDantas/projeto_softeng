"""Apresentação padronizada de mensagens ao usuário."""

import reflex as rx


ESTILOS_MENSAGEM = {
    "sucesso": {"fundo": "#e8f5ed", "borda": "#167d4b", "texto": "#14532d"},
    "informacao": {"fundo": "#eaf2f8", "borda": "#276749", "texto": "#183b32"},
    "erro": {"fundo": "#fff0ee", "borda": "#b42318", "texto": "#7f1d1d"},
}


def mensagem(texto: str, tipo: str = "informacao") -> rx.Component:
    """Cria uma mensagem visual de sucesso, informação ou erro."""

    if tipo not in ESTILOS_MENSAGEM:
        raise ValueError("O tipo da mensagem deve ser sucesso, informacao ou erro.")

    estilo = ESTILOS_MENSAGEM[tipo]
    return rx.box(
        rx.text(texto, color=estilo["texto"]),
        background_color=estilo["fundo"],
        border_left=f"4px solid {estilo['borda']}",
        border_radius="4px",
        padding="12px 16px",
        role="status" if tipo != "erro" else "alert",
        width="100%",
    )