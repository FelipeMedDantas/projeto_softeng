"""Repositório único em memória para dados compartilhados entre sessões."""

from copy import deepcopy
from threading import RLock
from typing import Callable, TypeVar, cast


T = TypeVar("T")


class RepositorioMemoria:
    """Coordena CRUD, configuração e reset com proteção contra concorrência."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._colecoes: dict[str, dict[str, object]] = {}
        self._configuracoes: dict[str, object] = {}

    def criar(
        self,
        colecao: str,
        registro: T,
        identificador: str | None = None,
    ) -> T:
        """Insere um registro novo e rejeita identificadores duplicados."""

        chave = identificador or getattr(registro, "id", None)
        if not isinstance(chave, str) or not chave:
            raise ValueError("O registro precisa de um identificador textual.")

        with self._lock:
            registros = self._colecoes.setdefault(colecao, {})
            if chave in registros:
                raise ValueError(f"Já existe um registro com o identificador {chave}.")
            registros[chave] = deepcopy(registro)
            return cast(T, deepcopy(registros[chave]))

    def obter(self, colecao: str, identificador: str) -> object | None:
        """Devolve uma cópia do registro ou None quando ele não existe."""

        with self._lock:
            registro = self._colecoes.get(colecao, {}).get(identificador)
            return deepcopy(registro) if registro is not None else None

    def listar(self, colecao: str) -> list[object]:
        """Devolve cópias dos registros de uma coleção."""

        with self._lock:
            return deepcopy(list(self._colecoes.get(colecao, {}).values()))

    def atualizar(
        self,
        colecao: str,
        identificador: str,
        registro: T,
    ) -> T:
        """Substitui um registro existente sem expor referências mutáveis."""

        with self._lock:
            registros = self._colecoes.get(colecao, {})
            if identificador not in registros:
                raise ValueError(f"Não existe registro com o identificador {identificador}.")
            chave_registro = getattr(registro, "id", identificador)
            if chave_registro != identificador:
                raise ValueError("O identificador do registro não pode ser alterado.")
            registros[identificador] = deepcopy(registro)
            return cast(T, deepcopy(registros[identificador]))

    def remover(self, colecao: str, identificador: str) -> bool:
        """Remove um registro e informa se ele existia."""

        with self._lock:
            registros = self._colecoes.get(colecao, {})
            return registros.pop(identificador, None) is not None

    def obter_configuracao(self, chave: str, padrao: T) -> T:
        """Lê uma configuração protegida pelo mesmo lock do repositório."""

        with self._lock:
            valor = self._configuracoes.get(chave, padrao)
            return cast(T, deepcopy(valor))

    def salvar_configuracao(self, chave: str, valor: object) -> None:
        """Salva uma configuração compartilhada sob o lock."""

        with self._lock:
            self._configuracoes[chave] = deepcopy(valor)

    def atualizar_configuracao(
        self,
        chave: str,
        padrao: T,
        transformacao: Callable[[T], T],
    ) -> T:
        """Lê, valida e grava uma configuração em uma única transação."""

        with self._lock:
            atual = cast(T, deepcopy(self._configuracoes.get(chave, padrao)))
            atualizado = transformacao(atual)
            self._configuracoes[chave] = deepcopy(atualizado)
            return cast(T, deepcopy(atualizado))

    def restaurar_estado_inicial(self) -> None:
        """Limpa as coleções e reconstroi o estado definido pelo seed."""

        with self._lock:
            self._colecoes.clear()
            self._configuracoes.clear()
            from app.dados.seed import carregar_seed

            carregar_seed(self)


_repositorio = RepositorioMemoria()


def obter_repositorio() -> RepositorioMemoria:
    """Devolve a instância única que compartilha dados entre sessões."""

    return _repositorio