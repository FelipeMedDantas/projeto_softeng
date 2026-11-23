"""Componente visual para a faixa de prioridade configurada."""

import reflex as rx

from app.dominio.parametros import ParametrosPrioridade, ler_parametros


CORES_FAIXA = {
    "alta": "#b42318",
    "media": "#c2410c",
    "baixa": "#167d4b",
}


def classificar_faixa(
    pontuacao: int,
    parametros: ParametrosPrioridade | None = None,
) -> str:
    """Classifica uma pontuação de 1 a 10 usando os limites configurados."""

    if not 1 <= pontuacao <= 10:
        raise ValueError("A pontuação deve estar entre 1 e 10.")

    configuracao = parametros or ler_parametros()
    if pontuacao >= configuracao.limite_alta:
        return "alta"
    if pontuacao >= configuracao.limite_media:
        return "media"
    return "baixa"


def faixa_cor(pontuacao: int) -> rx.Component:
    """Exibe a pontuação com a cor definida pelos parâmetros ativos."""

    faixa = classificar_faixa(pontuacao)
    rotulos = {
        "alta": "Prioridade alta",
        "media": "Prioridade média",
        "baixa": "Prioridade baixa",
    }
    return rx.box(
        rx.text(f"{rotulos[faixa]} · Pontuação {pontuacao}", font_weight="600"),
        background_color=CORES_FAIXA[faixa],
        border_radius="4px",
        color="white",
        padding="8px 12px",
        width="fit-content",
    )