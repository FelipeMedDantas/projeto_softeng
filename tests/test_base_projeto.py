"""Testes da fundação do projeto."""

from dataclasses import is_dataclass
from datetime import date, datetime
from concurrent.futures import ThreadPoolExecutor
import subprocess
import sys

import pytest

from app.dominio.modelos import (
    Atendimento,
    Paciente,
    PerfilUsuario,
    RegistroAuditoria,
    Sintoma,
    StatusAtendimento,
    Usuario,
)
from app.dominio.parametros import (
    PARAMETROS_PADRAO,
    ParametrosPrioridade,
    alterar_parametros,
    ler_parametros,
    restaurar_parametros,
)
from app.dados.repositorio import RepositorioMemoria
from app.dados.seed import carregar_seed
from app.componentes.faixa_cor import classificar_faixa


class ArmazenamentoConfiguracaoTeste:
    """Armazenamento isolado para testar os parâmetros sem estado global."""

    def __init__(self) -> None:
        self.configuracoes: dict[str, object] = {}

    def obter_configuracao(self, chave: str, padrao: object) -> object:
        return self.configuracoes.get(chave, padrao)

    def salvar_configuracao(self, chave: str, valor: object) -> None:
        self.configuracoes[chave] = valor

    def atualizar_configuracao(self, chave: str, padrao: object, transformacao):
        atual = self.configuracoes.get(chave, padrao)
        atualizado = transformacao(atual)
        self.configuracoes[chave] = atualizado
        return atualizado


def test_dominio_define_entidades_como_dataclasses() -> None:
    instante = datetime(2026, 1, 1, 10, 0)
    entidades = (
        Usuario("usuario-1", "Pessoa Fictícia", PerfilUsuario.ADMIN),
        Paciente("paciente-1", "Paciente Fictício", "00000000000", "P-001", date(1990, 1, 1)),
        Sintoma("sintoma-1", "Dor fictícia", 1),
        Atendimento("atendimento-1", "paciente-1", instante),
        RegistroAuditoria("auditoria-1", "usuario-1", "criar", "Paciente", "paciente-1", instante),
    )

    assert all(is_dataclass(entidade) for entidade in entidades)


def test_dominio_expoe_perfis_e_status_estaveis() -> None:
    assert {perfil.value for perfil in PerfilUsuario} == {
        "recepcao",
        "medico",
        "paciente",
        "admin",
    }
    assert {status.value for status in StatusAtendimento} == {
        "aguardando",
        "em_atendimento",
        "finalizado",
        "cancelado",
        "nao_compareceu",
    }


def test_dominio_importa_sem_reflex() -> None:
    script = """
import importlib
import pkgutil
import sys

class BloqueiaReflex:
    def find_spec(self, nome_completo, caminho=None, alvo=None):
        if nome_completo == "reflex" or nome_completo.startswith("reflex."):
            raise ModuleNotFoundError("Reflex não deve ser importado pelo domínio")

sys.meta_path.insert(0, BloqueiaReflex())
import app.dominio

for modulo in pkgutil.iter_modules(app.dominio.__path__):
    importlib.import_module(f"app.dominio.{modulo.name}")
"""
    resultado = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        text=True,
    )

    assert resultado.returncode == 0, resultado.stderr


def test_parametros_expoem_padroes_e_modificacoes_validas() -> None:
    armazenamento = ArmazenamentoConfiguracaoTeste()

    assert ler_parametros(armazenamento) == PARAMETROS_PADRAO
    parametros = alterar_parametros(armazenamento, modo_gravidade="soma")

    assert parametros.modo_gravidade.value == "soma"
    assert ler_parametros(armazenamento) == parametros


@pytest.mark.parametrize(
    ("alteracoes", "trecho_mensagem"),
    [
        ({"modo_gravidade": "desconhecido"}, "modo de gravidade"),
        ({"intervalo_bonus_min": 0}, "intervalo"),
        ({"capacidade_fila": 0}, "capacidade"),
        ({"limite_alta": 4}, "limite alto"),
    ],
)
def test_parametros_rejeitam_valores_invalidos_sem_alterar_estado(
    alteracoes: dict[str, object],
    trecho_mensagem: str,
) -> None:
    armazenamento = ArmazenamentoConfiguracaoTeste()
    anterior = ler_parametros(armazenamento)

    with pytest.raises(ValueError, match=trecho_mensagem):
        alterar_parametros(armazenamento, **alteracoes)

    assert ler_parametros(armazenamento) == anterior


def test_parametros_podem_ser_restaurados() -> None:
    armazenamento = ArmazenamentoConfiguracaoTeste()
    alterar_parametros(armazenamento, capacidade_fila=45)

    restaurados = restaurar_parametros(armazenamento)

    assert restaurados == PARAMETROS_PADRAO
    assert ler_parametros(armazenamento) == PARAMETROS_PADRAO


def test_repositorio_executa_crud_generico() -> None:
    repositorio = RepositorioMemoria()
    sintoma = Sintoma("sintoma-1", "Dor fictícia", 1)

    repositorio.criar("sintomas", sintoma)
    assert repositorio.obter("sintomas", "sintoma-1") == sintoma

    sintoma_atualizado = Sintoma("sintoma-1", "Dor fictícia atualizada", 2)
    repositorio.atualizar("sintomas", "sintoma-1", sintoma_atualizado)
    assert repositorio.listar("sintomas") == [sintoma_atualizado]

    assert repositorio.remover("sintomas", "sintoma-1") is True
    assert repositorio.obter("sintomas", "sintoma-1") is None
    assert repositorio.remover("sintomas", "sintoma-1") is False


def test_repositorio_recusa_duplicidade_e_atualizacao_inexistente() -> None:
    repositorio = RepositorioMemoria()
    sintoma = Sintoma("sintoma-1", "Dor fictícia", 1)
    repositorio.criar("sintomas", sintoma)

    with pytest.raises(ValueError, match="Já existe"):
        repositorio.criar("sintomas", sintoma)
    with pytest.raises(ValueError, match="Não existe"):
        repositorio.atualizar("sintomas", "inexistente", sintoma)


def test_repositorio_reconstroi_seed_ao_restaurar_estado() -> None:
    repositorio = RepositorioMemoria()
    carregar_seed(repositorio)
    repositorio.criar("sintomas", Sintoma("temporario", "Temporário", 1))

    repositorio.restaurar_estado_inicial()

    assert len(repositorio.listar("usuarios")) == 3
    assert len(repositorio.listar("sintomas")) == 10
    assert len(repositorio.listar("pacientes")) == 6
    assert repositorio.obter("sintomas", "temporario") is None


def test_seed_carrega_quantidades_e_cpfs_ficticios_validos() -> None:
    repositorio = RepositorioMemoria()

    carregar_seed(repositorio)
    carregar_seed(repositorio)

    usuarios = repositorio.listar("usuarios")
    sintomas = repositorio.listar("sintomas")
    pacientes = repositorio.listar("pacientes")
    assert {usuario.perfil for usuario in usuarios} == {
        PerfilUsuario.ADMIN,
        PerfilUsuario.RECEPCAO,
        PerfilUsuario.MEDICO,
    }
    assert len(usuarios) == 3
    assert len(sintomas) == 10
    assert {sintoma.gravidade for sintoma in sintomas} == set(range(1, 9))
    assert len(pacientes) == 6
    assert len({paciente.cpf for paciente in pacientes}) == 6
    assert all(_cpf_tem_digitos_validos(paciente.cpf) for paciente in pacientes)


def _cpf_tem_digitos_validos(cpf: str) -> bool:
    if len(cpf) != 11 or not cpf.isdigit() or len(set(cpf)) == 1:
        return False
    base = cpf[:9]
    primeiro_digito = _calcular_digito_teste(base)
    segundo_digito = _calcular_digito_teste(base + primeiro_digito)
    return cpf[-2:] == primeiro_digito + segundo_digito


def _calcular_digito_teste(base: str) -> str:
    soma = sum(int(digito) * peso for digito, peso in zip(base, range(len(base) + 1, 1, -1)))
    resto = (soma * 10) % 11
    return "0" if resto == 10 else str(resto)


def test_repositorio_grava_com_seguranca_concorrente_em_varias_threads() -> None:
    repositorio = RepositorioMemoria()

    def gravar_sintoma(indice: int) -> None:
        repositorio.criar(
            "sintomas",
            Sintoma(f"sintoma-{indice}", f"Sintoma fictício {indice}", indice % 8 + 1),
        )

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(gravar_sintoma, range(400)))

    assert len(repositorio.listar("sintomas")) == 400


@pytest.mark.parametrize(
    ("pontuacao", "faixa_esperada"),
    [(4, "baixa"), (5, "media"), (7, "media"), (8, "alta"), (10, "alta")],
)
def test_faixa_de_cor_respeita_limites_configurados(
    pontuacao: int,
    faixa_esperada: str,
) -> None:
    assert classificar_faixa(pontuacao, PARAMETROS_PADRAO) == faixa_esperada