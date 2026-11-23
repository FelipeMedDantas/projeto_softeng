"""Parâmetros de negócio e suas regras de validação."""

from dataclasses import dataclass, fields, replace
from enum import Enum
from typing import Callable, Protocol, TypeVar


class ModoGravidade(str, Enum):
    """Formas permitidas de combinar a gravidade dos sintomas."""

    MAIOR = "maior"
    SOMA = "soma"
    MEDIA = "media"


@dataclass(frozen=True)
class ParametrosPrioridade:
    """Configuração ajustável das regras futuras de priorização."""

    modo_gravidade: ModoGravidade = ModoGravidade.MAIOR
    idade_idoso: int = 60
    idade_crianca: int = 12
    prioridade_legal_pontos: int = 1
    intervalo_bonus_min: int = 30
    teto_bonus: int = 7
    limite_alta: int = 8
    limite_media: int = 5
    capacidade_fila: int = 30


PARAMETROS_PADRAO = ParametrosPrioridade()
CHAVE_PARAMETROS = "parametros_prioridade"
_TipoValor = TypeVar("_TipoValor")


class ArmazenamentoConfiguracao(Protocol):
    """Contrato mínimo para armazenar configuração no repositório central."""

    def obter_configuracao(self, chave: str, padrao: _TipoValor) -> _TipoValor:
        """Lê uma configuração compartilhada ou devolve seu padrão."""

    def salvar_configuracao(self, chave: str, valor: object) -> None:
        """Salva uma configuração compartilhada de forma segura."""

    def atualizar_configuracao(
        self,
        chave: str,
        padrao: _TipoValor,
        transformacao: Callable[[_TipoValor], _TipoValor],
    ) -> _TipoValor:
        """Atualiza uma configuração em transação protegida contra concorrência."""


def _obter_armazenamento(
    armazenamento: ArmazenamentoConfiguracao | None,
) -> ArmazenamentoConfiguracao:
    if armazenamento is not None:
        return armazenamento

    from app.dados.repositorio import obter_repositorio

    return obter_repositorio()


def ler_parametros(
    armazenamento: ArmazenamentoConfiguracao | None = None,
) -> ParametrosPrioridade:
    """Lê os parâmetros ativos ou os padrões do projeto."""

    return _obter_armazenamento(armazenamento).obter_configuracao(
        CHAVE_PARAMETROS,
        PARAMETROS_PADRAO,
    )


def validar_parametros(parametros: ParametrosPrioridade) -> None:
    """Recusa configurações inconsistentes com mensagens em português."""

    if not isinstance(parametros.modo_gravidade, ModoGravidade):
        raise ValueError("O modo de gravidade deve ser maior, soma ou media.")

    campos_inteiros = (
        "idade_idoso",
        "idade_crianca",
        "prioridade_legal_pontos",
        "intervalo_bonus_min",
        "teto_bonus",
        "limite_alta",
        "limite_media",
        "capacidade_fila",
    )
    for nome_campo in campos_inteiros:
        valor = getattr(parametros, nome_campo)
        if not isinstance(valor, int) or isinstance(valor, bool):
            raise ValueError(f"O parâmetro {nome_campo} deve ser um número inteiro.")

    if parametros.idade_idoso < 0 or parametros.idade_crianca < 0:
        raise ValueError("As idades de prioridade legal não podem ser negativas.")
    if parametros.prioridade_legal_pontos < 0:
        raise ValueError("Os pontos de prioridade legal não podem ser negativos.")
    if parametros.intervalo_bonus_min <= 0:
        raise ValueError("O intervalo do bônus deve ser maior que zero.")
    if parametros.teto_bonus < 0:
        raise ValueError("O teto do bônus não pode ser negativo.")
    if not 1 <= parametros.limite_media <= 10:
        raise ValueError("O limite médio deve estar entre 1 e 10.")
    if not 1 <= parametros.limite_alta <= 10:
        raise ValueError("O limite alto deve estar entre 1 e 10.")
    if parametros.limite_alta < parametros.limite_media:
        raise ValueError("O limite alto não pode ser menor que o limite médio.")
    if parametros.capacidade_fila < 1:
        raise ValueError("A capacidade da fila deve ser pelo menos 1.")


def alterar_parametros(
    armazenamento: ArmazenamentoConfiguracao | None = None,
    **alteracoes: object,
) -> ParametrosPrioridade:
    """Valida e salva uma atualização sem alterar o estado em caso de erro."""

    nomes_permitidos = {campo.name for campo in fields(ParametrosPrioridade)}
    nomes_desconhecidos = set(alteracoes) - nomes_permitidos
    if nomes_desconhecidos:
        nome_desconhecido = sorted(nomes_desconhecidos)[0]
        raise ValueError(f"Parâmetro desconhecido: {nome_desconhecido}.")

    valores = dict(alteracoes)
    if "modo_gravidade" in valores:
        try:
            valores["modo_gravidade"] = ModoGravidade(valores["modo_gravidade"])
        except ValueError:
            raise ValueError("O modo de gravidade deve ser maior, soma ou media.") from None

    armazenamento_ativo = _obter_armazenamento(armazenamento)

    def validar_e_atualizar(
        parametros_atuais: ParametrosPrioridade,
    ) -> ParametrosPrioridade:
        parametros_atualizados = replace(parametros_atuais, **valores)
        validar_parametros(parametros_atualizados)
        return parametros_atualizados

    return armazenamento_ativo.atualizar_configuracao(
        CHAVE_PARAMETROS,
        PARAMETROS_PADRAO,
        validar_e_atualizar,
    )


def restaurar_parametros(
    armazenamento: ArmazenamentoConfiguracao | None = None,
) -> ParametrosPrioridade:
    """Restaura e devolve todos os parâmetros padrão do projeto."""

    _obter_armazenamento(armazenamento).salvar_configuracao(
        CHAVE_PARAMETROS,
        PARAMETROS_PADRAO,
    )
    return PARAMETROS_PADRAO