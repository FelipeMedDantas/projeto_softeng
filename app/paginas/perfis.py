"""Páginas iniciais por perfil e respostas de erro da aplicação."""

import reflex as rx

from app.componentes.layout import layout_base


def _pagina_protegida(titulo: str, descricao: str) -> rx.Component:
    return layout_base(
        rx.vstack(
            rx.heading(titulo, color="#183b32", size="6"),
            rx.text(descricao, color="#42574f"),
            align_items="start",
            spacing="3",
            width="100%",
        )
    )


def recepcao() -> rx.Component:
    return _pagina_protegida("Recepção", "Área de recepção do sistema.")


def medico() -> rx.Component:
    return _pagina_protegida("Atendimentos", "Área médica do sistema.")


def paciente() -> rx.Component:
    return _pagina_protegida("Meu atendimento", "Área do paciente.")


def administracao() -> rx.Component:
    return _pagina_protegida("Administração", "Área administrativa do sistema.")


def perfil() -> rx.Component:
    return _pagina_protegida("Meu perfil", "Informações do perfil autenticado.")


def acesso_negado() -> rx.Component:
    return _pagina_erro(
        "Acesso negado",
        "Seu perfil não tem permissão para acessar esta página.",
    )


def nao_encontrada() -> rx.Component:
    return _pagina_erro(
        "Página não encontrada",
        "Não encontramos a página solicitada.",
    )


def _pagina_erro(titulo: str, descricao: str) -> rx.Component:
    return layout_base(
        rx.vstack(
            rx.heading(titulo, color="#183b32", size="6"),
            rx.text(descricao, color="#42574f"),
            rx.link("Voltar ao início", href="/", color="#183b32"),
            align_items="start",
            spacing="3",
            width="100%",
        ),
        mostrar_sair=False,
        mostrar_navegacao=False,
        mostrar_perfil=False,
        protegido=False,
    )


PAGINAS_PROTEGIDAS = {
    "/recepcao": (recepcao, "Recepção"),
    "/medico": (medico, "Atendimentos"),
    "/paciente": (paciente, "Meu atendimento"),
    "/admin": (administracao, "Administração"),
    "/perfil": (perfil, "Meu perfil"),
}