"""Modelos tipados do domínio do atendimento."""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum


class PerfilUsuario(str, Enum):
    """Perfis reconhecidos pelo sistema."""

    RECEPCAO = "recepcao"
    MEDICO = "medico"
    PACIENTE = "paciente"
    ADMIN = "admin"


class StatusAtendimento(str, Enum):
    """Estados possíveis de um atendimento."""

    AGUARDANDO = "aguardando"
    EM_ATENDIMENTO = "em_atendimento"
    FINALIZADO = "finalizado"
    CANCELADO = "cancelado"
    NAO_COMPARECEU = "nao_compareceu"


@dataclass
class Usuario:
    """Representa uma pessoa com acesso a um perfil do sistema."""

    id: str
    nome: str
    perfil: PerfilUsuario
    ativo: bool = True
    email: str = ""
    senha_hash: str = ""

    def __post_init__(self) -> None:
        self.email = self.email.strip().lower()


@dataclass
class TentativaLogin:
    """Estado temporário de falhas para um e-mail normalizado."""

    id: str
    falhas_consecutivas: int = 0
    bloqueado_ate: datetime | None = None


@dataclass
class SessaoAutenticada:
    """Sessão identificada somente pelo digest do token opaco."""

    id: str
    usuario_id: str
    criada_em: datetime
    ultima_atividade: datetime


@dataclass
class Paciente:
    """Representa um paciente com identificadores fictícios do projeto."""

    id: str
    nome: str
    cpf: str
    numero_paciente: str
    data_nascimento: date
    gestante: bool = False


@dataclass
class Sintoma:
    """Representa um sintoma e sua gravidade configurada."""

    id: str
    nome: str
    gravidade: int


@dataclass
class Atendimento:
    """Representa a entrada de um paciente na fila de atendimento."""

    id: str
    paciente_id: str
    criado_em: datetime
    sintomas_ids: list[str] = field(default_factory=list)
    status: StatusAtendimento = StatusAtendimento.AGUARDANDO
    pontuacao: int | None = None


@dataclass
class RegistroAuditoria:
    """Registra uma ação realizada no sistema."""

    id: str
    usuario_id: str | None
    acao: str
    entidade: str
    entidade_id: str
    criado_em: datetime
    detalhes: dict[str, str] = field(default_factory=dict)