"""Layout compartilhado da interface Reflex."""

import json

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

_SCRIPT_SESSAO = """
(async () => {
  try {
    const resposta = await fetch('/api/autenticacao/sessao', {
      method: 'GET',
      credentials: 'same-origin'
    });
    const corpo = await resposta.json();
    return JSON.stringify({sucesso: corpo.sucesso, perfil: corpo.perfil});
  } catch (erro) {
    return JSON.stringify({sucesso: false, perfil: null});
  }
})()
"""


class EstadoLayout(rx.State):
    """Mantém somente o rótulo visual do perfil confirmado pelo servidor."""

    perfil_exibicao: str = ""

    @rx.event
    def definir_perfil(self, perfil: str) -> None:
        if perfil in {item.value for item in MENUS_POR_PERFIL}:
            self.perfil_exibicao = perfil
        else:
            self.perfil_exibicao = ""

    @rx.event
    def limpar_perfil(self) -> None:
        self.perfil_exibicao = ""

    @rx.event
    def receber_sessao(
        self,
        resultado_json: str,
    ) -> rx.event.EventSpec | None:
        try:
            resultado = json.loads(resultado_json)
        except (json.JSONDecodeError, TypeError):
            self.perfil_exibicao = ""
            return rx.redirect("/login")

        perfil = resultado.get("perfil") if resultado.get("sucesso") is True else None
        if isinstance(perfil, str) and perfil in {item.value for item in MENUS_POR_PERFIL}:
            self.perfil_exibicao = perfil
            return None

        self.perfil_exibicao = ""
        return rx.redirect("/login")

    @rx.event
    def verificar_sessao(self) -> rx.event.EventSpec:
        self.perfil_exibicao = ""
        return rx.call_script(_SCRIPT_SESSAO, callback=EstadoLayout.receber_sessao)


def layout_base(
    conteudo: rx.Component,
    perfil: PerfilUsuario | None = None,
    mostrar_sair: bool = True,
    mostrar_navegacao: bool = True,
    mostrar_perfil: bool = True,
    protegido: bool = True,
) -> rx.Component:
    """Envolve conteúdo com cabeçalho e navegação visual responsiva."""

    perfil_atual: str | rx.Var[str] = (
        EstadoLayout.perfil_exibicao
        if protegido
        else (perfil.value if perfil is not None else "")
    )
    rotulo_perfil = rx.cond(
        perfil_atual == PerfilUsuario.ADMIN.value,
        ROTULOS_PERFIL[PerfilUsuario.ADMIN],
        rx.cond(
            perfil_atual == PerfilUsuario.MEDICO.value,
            ROTULOS_PERFIL[PerfilUsuario.MEDICO],
            rx.cond(
                perfil_atual == PerfilUsuario.PACIENTE.value,
                ROTULOS_PERFIL[PerfilUsuario.PACIENTE],
                ROTULOS_PERFIL[PerfilUsuario.RECEPCAO],
            ),
        ),
    )
    componentes_cabecalho = [
        rx.vstack(
            rx.text("PRONTO ATENDIMENTO FICTÍCIO", color="#276749", size="2"),
            rx.heading("Sistema de Priorização", color="#183b32", size="5"),
            align_items="start",
            spacing="1",
        ),
    ]
    if mostrar_perfil:
        componentes_cabecalho.append(
            rx.cond(
                perfil_atual != "",
                rx.text(
                    "Perfil: ",
                    rotulo_perfil,
                    color="#42574f",
                    font_weight="500",
                ),
                rx.fragment(),
            )
        )
    if mostrar_sair:
        componentes_cabecalho.append(
            rx.cond(
                perfil_atual != "",
                rx.button(
                    "Sair",
                    type="button",
                    variant="outline",
                    on_click=rx.call_script(
                        "fetch('/api/autenticacao/logout', "
                        "{method: 'POST', credentials: 'same-origin'})"
                        ".finally(() => window.location.assign('/login'))"
                    ),
                ),
                rx.fragment(),
            )
        )

    conteudos_layout = [
        rx.flex(
            *componentes_cabecalho,
            align="center",
            justify="between",
            flex_wrap="wrap",
            gap="12px",
            width="100%",
        ),
    ]
    if mostrar_navegacao:
        menu_perfil = rx.cond(
            perfil_atual == PerfilUsuario.RECEPCAO.value,
            rx.fragment(
                rx.link("Entrada", href="/", color="#183b32"),
                rx.link("Fila de espera", href="/", color="#183b32"),
            ),
            rx.cond(
                perfil_atual == PerfilUsuario.MEDICO.value,
                rx.fragment(
                    rx.link("Atendimentos", href="/", color="#183b32"),
                    rx.link("Pacientes", href="/", color="#183b32"),
                ),
                rx.cond(
                    perfil_atual == PerfilUsuario.ADMIN.value,
                    rx.fragment(
                        rx.link("Visão geral", href="/", color="#183b32"),
                        rx.link("Parâmetros", href="/", color="#183b32"),
                    ),
                    rx.fragment(),
                ),
            ),
        )
        navegacao = rx.flex(
            rx.link("Início", href="/", color="#183b32"),
            menu_perfil,
            flex_wrap="wrap",
            gap="12px 20px",
            width="100%",
        )
        conteudos_layout.append(
            rx.cond(
                perfil_atual != "",
                rx.box(
                    navegacao,
                    border_bottom="1px solid #d5dfd9",
                    padding_bottom="12px",
                    width="100%",
                ),
                rx.fragment(),
            )
        )
    conteudo_protegido = rx.box(conteudo, padding_y="24px", width="100%")
    conteudos_layout.append(
        rx.cond(
            perfil_atual != "",
            conteudo_protegido,
            rx.fragment(),
        )
        if protegido
        else conteudo_protegido
    )

    return rx.box(
        rx.vstack(
            *conteudos_layout,
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