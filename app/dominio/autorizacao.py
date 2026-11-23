"""Política de rotas e permissões associadas aos perfis do sistema."""

from types import MappingProxyType
from typing import Final
from urllib.parse import urlsplit

from app.dominio.modelos import PerfilUsuario


ROTAS_INICIAIS: Final = MappingProxyType(
    {
        PerfilUsuario.RECEPCAO: "/recepcao",
        PerfilUsuario.MEDICO: "/medico",
        PerfilUsuario.PACIENTE: "/paciente",
        PerfilUsuario.ADMIN: "/admin",
    }
)

PERFIS_POR_ROTA: Final = MappingProxyType(
    {
        "/recepcao": frozenset({PerfilUsuario.RECEPCAO}),
        "/medico": frozenset({PerfilUsuario.MEDICO}),
        "/paciente": frozenset({PerfilUsuario.PACIENTE}),
        "/admin": frozenset({PerfilUsuario.ADMIN}),
        "/perfil": frozenset(
            {
                PerfilUsuario.RECEPCAO,
                PerfilUsuario.MEDICO,
                PerfilUsuario.ADMIN,
            }
        ),
    }
)


def rota_inicial(perfil: PerfilUsuario) -> str:
    """Retorna a rota inicial definida para o perfil."""

    return ROTAS_INICIAIS[perfil]


def perfil_pode_acessar(perfil: PerfilUsuario, rota: str) -> bool:
    """Informa se o perfil está autorizado a acessar a rota protegida."""

    return perfil in PERFIS_POR_ROTA.get(rota, frozenset())


def rotas_autorizadas(perfil: PerfilUsuario) -> tuple[str, ...]:
    """Retorna as rotas protegidas autorizadas ao perfil, na ordem definida."""

    return tuple(
        rota
        for rota, perfis_permitidos in PERFIS_POR_ROTA.items()
        if perfil in perfis_permitidos
    )


def destino_pos_login(candidato: str | None, perfil: PerfilUsuario) -> str:
    """Aceita somente destinos locais registrados e autorizados ao perfil."""

    fallback = rota_inicial(perfil)
    if not isinstance(candidato, str) or not candidato:
        return fallback
    if "\\" in candidato or any(ord(caractere) < 32 for caractere in candidato):
        return fallback

    try:
        partes = urlsplit(candidato)
    except ValueError:
        return fallback

    if (
        partes.scheme
        or partes.netloc
        or partes.fragment
        or not partes.path.startswith("/")
        or partes.path.startswith("//")
    ):
        return fallback

    rota = partes.path.rstrip("/") or "/"
    if not perfil_pode_acessar(perfil, rota):
        return fallback

    return f"{rota}?{partes.query}" if partes.query else rota