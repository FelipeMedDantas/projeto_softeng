"""Carga idempotente de exemplos fictícios para desenvolvimento."""

from datetime import date
from typing import TYPE_CHECKING

from app.dominio.modelos import Paciente, PerfilUsuario, Sintoma, Usuario

if TYPE_CHECKING:
    from app.dados.repositorio import RepositorioMemoria


def _calcular_digito_cpf(base: str) -> str:
    soma = sum(int(digito) * peso for digito, peso in zip(base, range(len(base) + 1, 1, -1)))
    resto = (soma * 10) % 11
    return "0" if resto == 10 else str(resto)


def _gerar_cpf_ficticio(base: str) -> str:
    primeiro_digito = _calcular_digito_cpf(base)
    segundo_digito = _calcular_digito_cpf(base + primeiro_digito)
    return base + primeiro_digito + segundo_digito


def carregar_seed(repositorio: "RepositorioMemoria | None" = None) -> None:
    """Insere o conjunto inicial sem duplicar registros existentes."""

    if repositorio is None:
        from app.dados.repositorio import obter_repositorio

        repositorio = obter_repositorio()

    usuarios = (
        Usuario("usuario-admin", "Administração Fictícia", PerfilUsuario.ADMIN),
        Usuario("usuario-recepcao", "Recepção Fictícia", PerfilUsuario.RECEPCAO),
        Usuario("usuario-medico", "Médico Fictício", PerfilUsuario.MEDICO),
    )
    for usuario in usuarios:
        if repositorio.obter("usuarios", usuario.id) is None:
            repositorio.criar("usuarios", usuario)

    for indice in range(10):
        gravidade = indice % 8 + 1
        sintoma = Sintoma(
            f"sintoma-{indice + 1:02d}",
            f"Sintoma fictício {indice + 1}",
            gravidade,
        )
        if repositorio.obter("sintomas", sintoma.id) is None:
            repositorio.criar("sintomas", sintoma)

    for indice in range(6):
        base_cpf = f"90000000{indice + 1}"
        paciente = Paciente(
            id=f"paciente-{indice + 1:02d}",
            nome=f"Paciente Fictício {indice + 1}",
            cpf=_gerar_cpf_ficticio(base_cpf),
            numero_paciente=f"PAC-{indice + 1:04d}",
            data_nascimento=date(1980 + indice, 1, indice + 1),
        )
        if repositorio.obter("pacientes", paciente.id) is None:
            repositorio.criar("pacientes", paciente)