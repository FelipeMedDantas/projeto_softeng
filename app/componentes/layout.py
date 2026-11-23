"""Layout compartilhado da interface Reflex."""

import reflex as rx

from app.dominio.modelos import PerfilUsuario


ROTULOS_PERFIL = {
    PerfilUsuario.RECEPCAO: "Recepção",
    PerfilUsuario.MEDICO: "Médico",
    PerfilUsuario.PACIENTE: "Paciente",
    PerfilUsuario.ADMIN: "Administração",
}

MENUS_POR_PERFIL = {
    PerfilUsuario.RECEPCAO: ("Entrada", "Fila de espera"),
    PerfilUsuario.MEDICO: ("Atendimentos", "Pacientes"),
    PerfilUsuario.PACIENTE: ("Meu atendimento", "Acompanhar fila"),
    PerfilUsuario.ADMIN: ("Visão geral", "Parâmetros"),
}


def layout_base(
    conteudo: rx.Component,
    perfil: PerfilUsuario = PerfilUsuario.RECEPCAO,
) -> rx.Component:
    """Envolve conteúdo com cabeçalho e navegação visual responsiva."""

    navegacao = rx.flex(
        rx.link("Início", href="/", color="#183b32"),
        *(
            rx.link(rotulo, href="/", color="#183b32")
            for rotulo in MENUS_POR_PERFIL[perfil]
        ),
        flex_wrap="wrap",
        gap="12px 20px",
        width="100%",
    )

    return rx.box(
        rx.vstack(
            rx.flex(
                rx.vstack(
                    rx.text("PRONTO ATENDIMENTO FICTÍCIO", color="#276749", size="2"),
                    rx.heading("Sistema de Priorização", color="#183b32", size="5"),
                    align_items="start",
                    spacing="1",
                ),
                rx.text(
                    f"Perfil: {ROTULOS_PERFIL[perfil]}",
                    color="#42574f",
                    font_weight="500",
                ),
                align="center",
                justify="between",
                flex_wrap="wrap",
                gap="12px",
                width="100%",
            ),
            rx.box(navegacao, border_bottom="1px solid #d5dfd9", padding_bottom="12px", width="100%"),
            rx.box(conteudo, padding_y="24px", width="100%"),
            align_items="stretch",
            max_width="1120px",
            margin="0 auto",
            padding="20px 16px",
            spacing="4",
            width="100%",
        ),
        background_color="#f5f8f6",
        color="#183b32",
        min_height="100vh",
        width="100%",
    )