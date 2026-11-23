"""Tela de login da equipe."""

import json

import reflex as rx

from app.componentes.layout import layout_base
from app.componentes.mensagens import mensagem
from rxconfig import config


_API_URL_JS = json.dumps(config.api_url.rstrip("/"))


_SCRIPT_LOGIN = """
(async () => {
    const formulario = document.getElementById('formulario-login');
    const dados = Object.fromEntries(new FormData(formulario).entries());
    dados.next = new URLSearchParams(window.location.search).get('next');
        const resposta = await fetch(__API_URL__ + '/api/autenticacao/login', {
        method: 'POST',
            credentials: 'include',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(dados)
    });
    const corpo = await resposta.json();
    if (corpo.sucesso && typeof corpo.destino === 'string') {
        window.location.assign(corpo.destino);
  }
    return JSON.stringify({sucesso: corpo.sucesso, mensagem: corpo.mensagem, perfil: corpo.perfil});
})()
""".replace("__API_URL__", _API_URL_JS)

_SCRIPT_VALIDAR_SESSAO = """
(async () => {
  try {
        const parametros = new URLSearchParams(window.location.search);
        if (parametros.get('sessao') === 'expirada') {
            return JSON.stringify({sucesso: false, mensagem: 'Sua sessão expirou. Entre novamente.'});
        }
        const resposta = await fetch(__API_URL__ + '/api/autenticacao/sessao', {
      method: 'GET',
            credentials: 'include'
    });
    const corpo = await resposta.json();
    return JSON.stringify({sucesso: corpo.sucesso, mensagem: corpo.mensagem, perfil: corpo.perfil});
  } catch (erro) {
    return JSON.stringify({sucesso: false, mensagem: ''});
  }
})()
""".replace("__API_URL__", _API_URL_JS)


class EstadoLogin(rx.State):
    """Mantém somente estado visual, sem credenciais nem tokens."""

    mostrar_senha: bool = False
    texto_mensagem: str = ""
    mensagem_erro: bool = True

    @rx.event
    def alternar_senha(self) -> None:
        self.mostrar_senha = not self.mostrar_senha

    @rx.event
    def receber_resultado_login(self, resultado_json: str) -> rx.event.EventSpec | None:
        try:
            resultado = json.loads(resultado_json)
        except (json.JSONDecodeError, TypeError):
            self.texto_mensagem = "O servidor retornou uma resposta inválida."
            self.mensagem_erro = True
            return None

        if resultado.get("sucesso") is True:
            self.texto_mensagem = ""
            self.mensagem_erro = True
            return None

        self.texto_mensagem = str(resultado.get("mensagem") or "E-mail ou senha incorretos.")
        self.mensagem_erro = True
        return None

    @rx.event
    def receber_resultado_sessao(
        self,
        resultado_json: str,
    ) -> rx.event.EventSpec | list[rx.event.EventSpec] | None:
        try:
            resultado = json.loads(resultado_json)
        except (json.JSONDecodeError, TypeError):
            return None

        if resultado.get("sucesso") is True:
            self.texto_mensagem = ""
            self.mensagem_erro = True
            return rx.redirect("/")
        if resultado.get("mensagem") == "Sua sessão expirou. Entre novamente.":
            self.texto_mensagem = "Sua sessão expirou. Entre novamente."
            self.mensagem_erro = False
        else:
            self.texto_mensagem = ""
            self.mensagem_erro = True
        return None

    @rx.event
    def verificar_sessao(self) -> rx.event.EventSpec:
        self.mostrar_senha = False
        self.texto_mensagem = ""
        self.mensagem_erro = True
        return rx.call_script(
            _SCRIPT_VALIDAR_SESSAO,
            callback=EstadoLogin.receber_resultado_sessao,
        )


def login() -> rx.Component:
    """Apresenta o formulário sem transportar credenciais pelo estado Reflex."""

    formulario = rx.form(
        rx.vstack(
            rx.box(
                rx.text("E-mail", font_weight="500", margin_bottom="6px"),
                rx.input(
                    id="campo-email-login",
                    name="email",
                    type="email",
                    placeholder="nome@exemplo.com",
                    auto_complete=True,
                    required=True,
                    width="100%",
                ),
                width="100%",
            ),
            rx.box(
                rx.text("Senha", font_weight="500", margin_bottom="6px"),
                rx.flex(
                    rx.input(
                        id="campo-senha-login",
                        name="senha",
                        type=rx.cond(EstadoLogin.mostrar_senha, "text", "password"),
                        placeholder="Digite sua senha",
                        auto_complete=True,
                        required=True,
                        width="100%",
                    ),
                    rx.button(
                        rx.cond(EstadoLogin.mostrar_senha, "Ocultar senha", "Mostrar senha"),
                        id="botao-mostrar-senha",
                        type="button",
                        variant="outline",
                        on_click=EstadoLogin.alternar_senha,
                        flex_shrink="0",
                    ),
                    align="center",
                    gap="8px",
                    width="100%",
                ),
                width="100%",
            ),
            rx.cond(
                EstadoLogin.texto_mensagem != "",
                rx.cond(
                    EstadoLogin.mensagem_erro,
                    mensagem(EstadoLogin.texto_mensagem, "erro"),
                    mensagem(EstadoLogin.texto_mensagem, "informacao"),
                ),
                rx.fragment(),
            ),
            rx.button(
                "Entrar",
                id="botao-entrar",
                type="submit",
                width="100%",
            ),
            align_items="stretch",
            spacing="4",
            width="100%",
        ),
        id="formulario-login",
        on_submit=rx.call_script(
            _SCRIPT_LOGIN,
            callback=EstadoLogin.receber_resultado_login,
        ),
        width="100%",
    )

    conteudo = rx.flex(
        rx.vstack(
            rx.heading("Entrar na equipe", color="#183b32", size="5"),
            rx.text("Acesse com seu e-mail e senha de equipe.", color="#42574f"),
            formulario,
            align_items="stretch",
            spacing="4",
            width="100%",
            max_width="420px",
            padding="24px",
            background_color="white",
            border="1px solid #d5dfd9",
            border_radius="6px",
        ),
        justify="center",
        width="100%",
    )
    return layout_base(
        conteudo,
        perfil=None,
        mostrar_sair=False,
        mostrar_navegacao=False,
        mostrar_perfil=False,
        protegido=False,
    )