"""Verificações de perfil para operações executadas por serviços."""

from collections.abc import Collection
from datetime import datetime, timezone
import re
from typing import TYPE_CHECKING

from app.dominio.modelos import PerfilUsuario, Usuario

if TYPE_CHECKING:
    from app.dados.repositorio import RepositorioMemoria


_CODIGO_OPERACAO = re.compile(r"[a-z][a-z0-9_]{0,63}")


def exigir_perfil_para_operacao(
    usuario: Usuario | None,
    perfis_permitidos: Collection[PerfilUsuario],
    operacao: str,
    *,
    agora: datetime | None = None,
    repositorio: "RepositorioMemoria | None" = None,
) -> None:
    """Rejeita e audita a operação antes de qualquer mutação do serviço."""

    if _CODIGO_OPERACAO.fullmatch(operacao) is None:
        raise ValueError("A operação de autorização deve ser um identificador técnico válido.")

    if usuario is not None and usuario.ativo and usuario.perfil in perfis_permitidos:
        return

    if repositorio is None:
        from app.dados.repositorio import obter_repositorio

        repositorio = obter_repositorio()

    repositorio.registrar_evento_acesso_negado(
        usuario.id if isinstance(usuario, Usuario) else None,
        operacao,
        agora or datetime.now(timezone.utc),
    )
    raise PermissionError("Você não tem permissão para realizar esta operação.")