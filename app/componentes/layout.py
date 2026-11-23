"""Layout compartilhado da interface Reflex."""

import json
from http.cookies import CookieError, SimpleCookie
from urllib.parse import urlencode

import reflex as rx

from app.dominio.autorizacao import ROTAS_INICIAIS, rotas_autorizadas
from app.dominio.modelos import PerfilUsuario
from app.dados.repositorio import obter_repositorio
from app.paginas.endpoints_autenticacao import NOME_COOKIE_SESSAO
from app.servicos.autenticacao import validar_sessao
from rxconfig import config


_API_URL_JS = json.dumps(config.api_url.rstrip("/"))


ROTULOS_PERFIL = {
    PerfilUsuario.RECEPCAO: "Recepção",
    PerfilUsuario.MEDICO: "Médico",
    PerfilUsuario.PACIENTE: "Paciente",
    PerfilUsuario.ADMIN: "Administração",
}

ROTULOS_ROTA = {
    "/recepcao": "Recepção",
    "/medico": "Atendimentos",
    "/paciente": "Meu atendimento",
    "/admin": "Administração",
    "/perfil": "Meu perfil",
}

_SCRIPT_LOGOUT = (
    f"fetch({_API_URL_JS} + '/api/autenticacao/logout', "
    "{method: 'POST', credentials: 'include'})"
    ".finally(() => window.location.assign('/login'))"
)


def links_navegacao_perfil(perfil: str) -> list[dict[str, str]]:
    """Cria somente links presentes na política do perfil informado."""

    try:
        perfil_enum = PerfilUsuario(perfil)
    except ValueError:
        return []

    return [
        {"rota": rota, "rotulo": ROTULOS_ROTA[rota]}
        for rota in rotas_autorizadas(perfil_enum)
    ]


def acesso_confirmado_para_rota(
    perfil: str,
    rota_atual: str,
    rota_verificada: str,
) -> bool:
    """Exibe conteúdo somente para a rota verificada do perfil autenticado."""

    try:
        perfil_enum = PerfilUsuario(perfil)
    except ValueError:
        return False

    rota = rota_atual.rstrip("/") or "/"
    return rota_verificada == rota and rota in rotas_autorizadas(perfil_enum)


def decidir_redirecionamento_guardia(
    autenticado: bool,
    perfil: PerfilUsuario | None,
    rota: str,
    mensagem: str,
) -> str | None:
    """Decide o destino após validar sessão e permissão para a rota atual."""

    rota_normalizada = rota.rstrip("/") or "/"
    if not autenticado or perfil is None:
        parametros: dict[str, str] = {}
        if mensagem == "Sua sessão expirou. Entre novamente.":
            parametros["sessao"] = "expirada"
        if rota_normalizada != "/":
            parametros["next"] = rota_normalizada
        return f"/login?{urlencode(parametros)}" if parametros else "/login"

    if rota_normalizada == "/":
        return ROTAS_INICIAIS[perfil]
    if rota_normalizada not in rotas_autorizadas(perfil):
        return "/403"
    return None


class EstadoLayout(rx.State):
    """Mantém somente o rótulo visual do perfil confirmado pelo servidor."""

    _perfil_exibicao: str = ""
    _rota_verificada: str = ""

    @rx.var
    def perfil_exibicao(self) -> str:
        return self._perfil_exibicao

    @rx.var
    def acesso_permitido(self) -> bool:
        return acesso_confirmado_para_rota(
            self._perfil_exibicao,
            self.router.url.path,
            self._rota_verificada,
        )

    @rx.var
    def links_navegacao(self) -> list[dict[str, str]]:
        return links_navegacao_perfil(self.perfil_exibicao)

    @rx.event
    def verificar_sessao(self) -> rx.event.EventSpec | None:
        self._perfil_exibicao = ""
        self._rota_verificada = ""
        rota = self.router.url.path.rstrip("/") or "/"

        cookies = SimpleCookie()
        try:
            cookies.load(self.router.headers.cookie or "")
        except CookieError:
            cookies = SimpleCookie()
        cookie_sessao = cookies.get(NOME_COOKIE_SESSAO)
        resultado = validar_sessao(
            cookie_sessao.value if cookie_sessao is not None else None,
            repositorio=obter_repositorio(),
        )
        destino = decidir_redirecionamento_guardia(
            resultado.sucesso,
            resultado.perfil,
            rota,
            resultado.mensagem,
        )
        if destino is not None:
            return rx.redirect(destino)

        if resultado.perfil is None:
            return rx.redirect("/login")

        self._perfil_exibicao = resultado.perfil.value
        self._rota_verificada = rota
        return None


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
    layout_autorizado: bool | rx.Var[bool] = (
        EstadoLayout.acesso_permitido if protegido else True
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
                layout_autorizado & (perfil_atual != ""),
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
                layout_autorizado & (perfil_atual != ""),
                rx.button(
                    "Sair",
                    type="button",
                    variant="outline",
                    on_click=rx.call_script(_SCRIPT_LOGOUT),
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
        menu_perfil = rx.foreach(
            EstadoLayout.links_navegacao,
            lambda link: rx.link(
                link["rotulo"],
                href=link["rota"],
                color="#183b32",
            ),
        )
        navegacao = rx.flex(
            menu_perfil,
            flex_wrap="wrap",
            gap="12px 20px",
            width="100%",
        )
        conteudos_layout.append(
            rx.cond(
                layout_autorizado,
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