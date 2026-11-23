"""Testes de autenticação da equipe."""

import pytest

from app.dados.repositorio import RepositorioMemoria
from app.dados.seed import carregar_seed
from app.dominio.modelos import PerfilUsuario, Usuario
from app.dominio.parametros import (
    PARAMETROS_PADRAO,
    ParametrosPrioridade,
    alterar_parametros,
    ler_parametros,
    restaurar_parametros,
)
import app.servicos.autenticacao as autenticacao


def test_usuario_normaliza_email_e_preserva_campos_existentes() -> None:
    usuario = Usuario(
        "usuario-1",
        "Pessoa Fictícia",
        PerfilUsuario.ADMIN,
        True,
        "  Admin@Example.Test ",
        "hash-ficticio",
    )

    assert usuario.email == "admin@example.test"
    assert usuario.senha_hash == "hash-ficticio"
    assert usuario.ativo is True


def test_usuario_repositorio_recusa_email_duplicado_ao_criar_e_atualizar() -> None:
    repositorio = RepositorioMemoria()
    primeiro = Usuario(
        "usuario-1",
        "Pessoa Fictícia 1",
        PerfilUsuario.ADMIN,
        email="admin@example.test",
    )
    segundo = Usuario(
        "usuario-2",
        "Pessoa Fictícia 2",
        PerfilUsuario.MEDICO,
        email="medico@example.test",
    )
    repositorio.criar("usuarios", primeiro)
    repositorio.criar("usuarios", segundo)

    with pytest.raises(ValueError, match="Já existe um usuário com esse e-mail"):
        repositorio.criar(
            "usuarios",
            Usuario(
                "usuario-3",
                "Pessoa Fictícia 3",
                PerfilUsuario.RECEPCAO,
                email="ADMIN@example.test",
            ),
        )

    segundo.email = " ADMIN@example.test "
    with pytest.raises(ValueError, match="Já existe um usuário com esse e-mail"):
        repositorio.atualizar("usuarios", "usuario-2", segundo)


def test_parametros_de_autenticacao_expoem_padroes_e_restauram() -> None:
    repositorio = RepositorioMemoria()

    assert PARAMETROS_PADRAO.tempo_sessao_min == 30
    assert PARAMETROS_PADRAO.max_tentativas_login == 5
    assert PARAMETROS_PADRAO.tempo_bloqueio_min == 5
    assert PARAMETROS_PADRAO.iteracoes_hash_senha == 600000

    alterar_parametros(repositorio, tempo_sessao_min=45)
    restaurados = restaurar_parametros(repositorio)

    assert restaurados == PARAMETROS_PADRAO
    assert ler_parametros(repositorio) == PARAMETROS_PADRAO


@pytest.mark.parametrize(
    "nome_parametro",
    [
        "tempo_sessao_min",
        "max_tentativas_login",
        "tempo_bloqueio_min",
        "iteracoes_hash_senha",
    ],
)
@pytest.mark.parametrize("valor_invalido", [0, -1])
def test_parametros_de_autenticacao_rejeitam_valores_nao_positivos(
    nome_parametro: str,
    valor_invalido: int,
) -> None:
    repositorio = RepositorioMemoria()
    anterior = ler_parametros(repositorio)

    with pytest.raises(ValueError, match="deve ser maior que zero"):
        alterar_parametros(repositorio, **{nome_parametro: valor_invalido})

    assert ler_parametros(repositorio) == anterior


def test_hash_de_senha_verifica_senha_correta_e_incorreta(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parametros_teste = ParametrosPrioridade(iteracoes_hash_senha=1000)
    monkeypatch.setattr(autenticacao, "ler_parametros", lambda: parametros_teste)

    senha = "DemoAdmin-02!"
    senha_hash = autenticacao.criar_hash_senha(senha)

    assert autenticacao.verificar_senha(senha, senha_hash) is True
    assert autenticacao.verificar_senha("senha-incorreta", senha_hash) is False
    assert senha not in senha_hash


def test_hash_de_senhas_iguais_usa_salts_diferentes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parametros_teste = ParametrosPrioridade(iteracoes_hash_senha=1000)
    monkeypatch.setattr(autenticacao, "ler_parametros", lambda: parametros_teste)

    primeiro_hash = autenticacao.criar_hash_senha("senha fictícia")
    segundo_hash = autenticacao.criar_hash_senha("senha fictícia")

    assert primeiro_hash != segundo_hash
    assert autenticacao.verificar_senha("senha fictícia", primeiro_hash) is True
    assert autenticacao.verificar_senha("senha fictícia", segundo_hash) is True


def test_hash_malformado_nao_verifica() -> None:
    assert autenticacao.verificar_senha("qualquer senha", "hash-inválido") is False


def test_seed_cria_contas_ficticias_com_hash_idempotente(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parametros_teste = ParametrosPrioridade(iteracoes_hash_senha=1000)
    monkeypatch.setattr(autenticacao, "ler_parametros", lambda: parametros_teste)
    repositorio = RepositorioMemoria()

    carregar_seed(repositorio)
    hashes_iniciais = {
        usuario.email: usuario.senha_hash
        for usuario in repositorio.listar("usuarios")
    }
    carregar_seed(repositorio)
    usuarios = repositorio.listar("usuarios")
    por_email = {usuario.email: usuario for usuario in usuarios}
    senhas_demo = {
        "admin@example.test": "DemoAdmin-02!",
        "recepcao@example.test": "DemoRecepcao-02!",
        "medico@example.test": "DemoMedico-02!",
    }

    assert set(por_email) == set(senhas_demo)
    assert len(usuarios) == 3
    assert all(usuario.senha_hash for usuario in usuarios)
    assert all(not hasattr(usuario, "senha") for usuario in usuarios)
    assert {usuario.email: usuario.senha_hash for usuario in usuarios} == hashes_iniciais
    assert all(
        autenticacao.verificar_senha(senha, por_email[email].senha_hash)
        for email, senha in senhas_demo.items()
    )


def test_seed_global_carrega_e_permite_login_sem_chamada_manual() -> None:
    from app.dados.repositorio import obter_repositorio
    from datetime import datetime, timezone

    repositorio = obter_repositorio()
    usuarios = repositorio.listar("usuarios")
    credenciais = (
        ("  ADMIN@EXAMPLE.TEST  ", "DemoAdmin-02!", "usuario-admin"),
        (" RECEPCAO@example.test ", "DemoRecepcao-02!", "usuario-recepcao"),
        (" MEDICO@example.test ", "DemoMedico-02!", "usuario-medico"),
    )
    resultados = [
        autenticacao.autenticar(
            email,
            senha,
            agora=datetime(2026, 11, 23, 12, 0, indice, tzinfo=timezone.utc),
        )
        for indice, (email, senha, _) in enumerate(credenciais)
    ]

    assert len(usuarios) == 3
    assert all(resultado.sucesso for resultado in resultados)
    assert [resultado.usuario_id for resultado in resultados] == [
        usuario_id for _, _, usuario_id in credenciais
    ]


def test_repositorio_conta_falhas_bloqueia_e_libera_apos_prazo() -> None:
    from datetime import datetime, timedelta, timezone

    repositorio = RepositorioMemoria()
    agora = datetime(2026, 11, 23, 12, 0, tzinfo=timezone.utc)

    for indice in range(5):
        tentativa = repositorio.registrar_falha_login(
            "admin@example.test",
            agora + timedelta(seconds=indice),
            max_tentativas=5,
            tempo_bloqueio_min=5,
        )
    instante_bloqueio = agora + timedelta(seconds=4)
    assert tentativa.falhas_consecutivas == 5
    assert tentativa.bloqueado_ate == instante_bloqueio + timedelta(minutes=5)

    bloqueada = repositorio.registrar_falha_login(
        "admin@example.test",
        agora + timedelta(minutes=1),
        max_tentativas=5,
        tempo_bloqueio_min=5,
    )
    assert bloqueada.falhas_consecutivas == 5
    assert repositorio.obter_tentativa_login(
        "admin@example.test",
        instante_bloqueio + timedelta(minutes=5),
    ) is None

    liberada = repositorio.registrar_falha_login(
        "admin@example.test",
        instante_bloqueio + timedelta(minutes=5),
        max_tentativas=5,
        tempo_bloqueio_min=5,
    )
    assert liberada.falhas_consecutivas == 1
    assert repositorio.limpar_tentativas_login("admin@example.test") is True


def test_repositorio_atualiza_tentativas_concorrentes_sem_perdas() -> None:
    from concurrent.futures import ThreadPoolExecutor
    from datetime import datetime, timezone

    repositorio = RepositorioMemoria()
    agora = datetime(2026, 11, 23, 12, 0, tzinfo=timezone.utc)

    def registrar_falha(_: int) -> None:
        repositorio.registrar_falha_login(
            "admin@example.test",
            agora,
            max_tentativas=1000,
            tempo_bloqueio_min=5,
        )

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(registrar_falha, range(200)))

    tentativa = repositorio.obter_tentativa_login("admin@example.test", agora)
    assert tentativa is not None
    assert tentativa.falhas_consecutivas == 200


def test_repositorio_renova_expira_e_invalida_sessao() -> None:
    from datetime import datetime, timedelta, timezone

    from app.dominio.modelos import SessaoAutenticada

    repositorio = RepositorioMemoria()
    agora = datetime(2026, 11, 23, 12, 0, tzinfo=timezone.utc)
    repositorio.criar_sessao(SessaoAutenticada("digest-1", "usuario-1", agora, agora))

    sessao, expirou = repositorio.renovar_sessao(
        "digest-1",
        agora + timedelta(minutes=10),
        tempo_sessao_min=30,
    )
    assert expirou is False
    assert sessao is not None
    assert sessao.ultima_atividade == agora + timedelta(minutes=10)

    sessao, expirou = repositorio.renovar_sessao(
        "digest-1",
        agora + timedelta(minutes=40),
        tempo_sessao_min=30,
    )
    assert sessao is None
    assert expirou is True

    repositorio.criar_sessao(SessaoAutenticada("digest-2", "usuario-1", agora, agora))
    sessao_invalidada = repositorio.invalidar_sessao("digest-2")
    assert sessao_invalidada is not None
    assert sessao_invalidada.usuario_id == "usuario-1"
    sessao, expirou = repositorio.renovar_sessao(
        "digest-2",
        agora,
        tempo_sessao_min=30,
    )
    assert sessao is None
    assert expirou is False


def test_repositorio_auditoria_eventos_sem_credenciais_ou_email() -> None:
    from datetime import datetime, timezone

    repositorio = RepositorioMemoria()
    agora = datetime(2026, 11, 23, 12, 0, tzinfo=timezone.utc)
    eventos = (
        ("login_sucesso", "usuario-admin"),
        ("login_falhou", None),
        ("login_bloqueado", None),
        ("logout", "usuario-admin"),
    )

    for acao, usuario_id in eventos:
        repositorio.registrar_evento_autenticacao(acao, usuario_id, agora)

    registros = repositorio.listar("auditoria")
    assert {registro.acao for registro in registros} == {
        "login_sucesso",
        "login_falhou",
        "login_bloqueado",
        "logout",
    }
    assert all(registro.detalhes == {} for registro in registros)
    assert all(registro.criado_em == agora for registro in registros)
    assert all("@" not in repr(registro) for registro in registros)
    assert "DemoAdmin-02!" not in repr(registros)
    assert "senha_hash" not in repr(registros)
    assert "digest-token" not in repr(registros)


def test_repositorio_auditoria_recusa_acao_arbitraria() -> None:
    from datetime import datetime, timezone

    repositorio = RepositorioMemoria()

    with pytest.raises(ValueError, match="ação de autenticação"):
        repositorio.registrar_evento_autenticacao(
            "senha=secreta",
            None,
            datetime(2026, 11, 23, 12, 0, tzinfo=timezone.utc),
        )

    assert repositorio.listar("auditoria") == []


@pytest.fixture
def repositorio_com_seed_login(monkeypatch: pytest.MonkeyPatch) -> RepositorioMemoria:
    parametros_teste = ParametrosPrioridade(iteracoes_hash_senha=1000)
    monkeypatch.setattr(
        autenticacao,
        "ler_parametros",
        lambda armazenamento=None: parametros_teste,
    )
    repositorio = RepositorioMemoria()
    carregar_seed(repositorio)
    return repositorio


def test_login_valido_cria_sessao_para_perfil_correto(
    repositorio_com_seed_login: RepositorioMemoria,
) -> None:
    import hashlib
    from datetime import datetime, timezone

    resultado = autenticacao.autenticar(
        " ADMIN@EXAMPLE.TEST ",
        "DemoAdmin-02!",
        agora=datetime(2026, 11, 23, 12, 0, tzinfo=timezone.utc),
        repositorio=repositorio_com_seed_login,
    )

    assert resultado.sucesso is True
    assert resultado.usuario_id == "usuario-admin"
    assert resultado.perfil is PerfilUsuario.ADMIN
    assert resultado.token_sessao
    assert resultado.token_sessao not in repr(resultado)
    digest = hashlib.sha256(resultado.token_sessao.encode("utf-8")).hexdigest()
    sessao = repositorio_com_seed_login.obter("sessoes", digest)
    assert sessao is not None
    assert sessao.id != resultado.token_sessao


def test_login_invalido_retorna_mensagem_generica(
    repositorio_com_seed_login: RepositorioMemoria,
) -> None:
    from datetime import datetime, timezone

    agora = datetime(2026, 11, 23, 12, 0, tzinfo=timezone.utc)
    senha_incorreta = autenticacao.autenticar(
        "admin@example.test",
        "senha-incorreta",
        agora=agora,
        repositorio=repositorio_com_seed_login,
    )
    email_inexistente = autenticacao.autenticar(
        "inexistente@example.test",
        "senha-incorreta",
        agora=agora,
        repositorio=repositorio_com_seed_login,
    )

    assert senha_incorreta.sucesso is False
    assert senha_incorreta.mensagem == "E-mail ou senha incorretos."
    assert email_inexistente.sucesso is False
    assert email_inexistente.mensagem == "E-mail ou senha incorretos."


def test_login_bloqueia_na_quinta_falha_e_libera_apos_cinco_minutos(
    repositorio_com_seed_login: RepositorioMemoria,
) -> None:
    from datetime import datetime, timedelta, timezone

    agora = datetime(2026, 11, 23, 12, 0, tzinfo=timezone.utc)
    for indice in range(5):
        resultado = autenticacao.autenticar(
            "admin@example.test",
            "senha-incorreta",
            agora=agora + timedelta(seconds=indice),
            repositorio=repositorio_com_seed_login,
        )

    assert resultado.sucesso is False
    assert resultado.mensagem == "Acesso bloqueado. Tente novamente em 5 minutos."

    instante_bloqueio = agora + timedelta(seconds=4)
    durante_bloqueio = autenticacao.autenticar(
        "admin@example.test",
        "DemoAdmin-02!",
        agora=instante_bloqueio + timedelta(minutes=3),
        repositorio=repositorio_com_seed_login,
    )
    assert durante_bloqueio.sucesso is False
    assert durante_bloqueio.mensagem == "Acesso bloqueado. Tente novamente em 2 minutos."

    liberado = autenticacao.autenticar(
        "admin@example.test",
        "DemoAdmin-02!",
        agora=instante_bloqueio + timedelta(minutes=5),
        repositorio=repositorio_com_seed_login,
    )
    assert liberado.sucesso is True
    assert repositorio_com_seed_login.obter_tentativa_login(
        "admin@example.test",
        instante_bloqueio + timedelta(minutes=5),
    ) is None


def test_login_recusa_usuario_desativado(
    repositorio_com_seed_login: RepositorioMemoria,
) -> None:
    from datetime import datetime, timezone

    usuario = repositorio_com_seed_login.obter("usuarios", "usuario-admin")
    usuario.ativo = False
    repositorio_com_seed_login.atualizar("usuarios", usuario.id, usuario)

    resultado = autenticacao.autenticar(
        "admin@example.test",
        "DemoAdmin-02!",
        agora=datetime(2026, 11, 23, 12, 0, tzinfo=timezone.utc),
        repositorio=repositorio_com_seed_login,
    )

    assert resultado.sucesso is False
    assert resultado.mensagem == "Conta desativada. Procure a administração."
    assert repositorio_com_seed_login.listar("sessoes") == []


def test_login_valido_zera_tentativas_consecutivas(
    repositorio_com_seed_login: RepositorioMemoria,
) -> None:
    from datetime import datetime, timedelta, timezone

    agora = datetime(2026, 11, 23, 12, 0, tzinfo=timezone.utc)
    for indice in range(3):
        autenticacao.autenticar(
            "admin@example.test",
            "senha-incorreta",
            agora=agora + timedelta(seconds=indice),
            repositorio=repositorio_com_seed_login,
        )

    resultado = autenticacao.autenticar(
        "admin@example.test",
        "DemoAdmin-02!",
        agora=agora + timedelta(seconds=5),
        repositorio=repositorio_com_seed_login,
    )

    assert resultado.sucesso is True
    assert repositorio_com_seed_login.obter_tentativa_login(
        "admin@example.test",
        agora + timedelta(seconds=5),
    ) is None


def test_sessao_renova_atividade_e_expira_apos_trinta_minutos(
    repositorio_com_seed_login: RepositorioMemoria,
) -> None:
    from datetime import datetime, timedelta, timezone

    agora = datetime(2026, 11, 23, 12, 0, tzinfo=timezone.utc)
    login = autenticacao.autenticar(
        "admin@example.test",
        "DemoAdmin-02!",
        agora=agora,
        repositorio=repositorio_com_seed_login,
    )
    assert login.token_sessao is not None

    atividade = autenticacao.validar_sessao(
        login.token_sessao,
        agora=agora + timedelta(minutes=10),
        repositorio=repositorio_com_seed_login,
    )
    assert atividade.sucesso is True

    ainda_ativa = autenticacao.validar_sessao(
        login.token_sessao,
        agora=agora + timedelta(minutes=39),
        repositorio=repositorio_com_seed_login,
    )
    assert ainda_ativa.sucesso is True

    expirada = autenticacao.validar_sessao(
        login.token_sessao,
        agora=agora + timedelta(minutes=69),
        repositorio=repositorio_com_seed_login,
    )
    assert expirada.sucesso is False
    assert expirada.mensagem == "Sua sessão expirou. Entre novamente."
    assert repositorio_com_seed_login.listar("sessoes") == []


def test_logout_invalida_sessao_e_impede_reabertura(
    repositorio_com_seed_login: RepositorioMemoria,
) -> None:
    from datetime import datetime, timedelta, timezone

    agora = datetime(2026, 11, 23, 12, 0, tzinfo=timezone.utc)
    login = autenticacao.autenticar(
        "recepcao@example.test",
        "DemoRecepcao-02!",
        agora=agora,
        repositorio=repositorio_com_seed_login,
    )
    assert login.token_sessao is not None

    logout = autenticacao.encerrar_sessao(
        login.token_sessao,
        agora=agora + timedelta(minutes=1),
        repositorio=repositorio_com_seed_login,
    )
    retorno_historico = autenticacao.validar_sessao(
        login.token_sessao,
        agora=agora + timedelta(minutes=2),
        repositorio=repositorio_com_seed_login,
    )

    assert logout.sucesso is True
    assert logout.mensagem == "Sessão encerrada."
    assert retorno_historico.sucesso is False
    assert retorno_historico.mensagem == "Entre para continuar."
    assert repositorio_com_seed_login.listar("sessoes") == []
    assert [
        registro.acao
        for registro in repositorio_com_seed_login.listar("auditoria")
    ].count("logout") == 1


def test_endpoint_login_define_cookie_seguro_sem_token_no_json(
    monkeypatch: pytest.MonkeyPatch,
    repositorio_com_seed_login: RepositorioMemoria,
) -> None:
    import hashlib

    from starlette.testclient import TestClient

    import app.paginas.endpoints_autenticacao as endpoints

    monkeypatch.setattr(endpoints, "obter_repositorio", lambda: repositorio_com_seed_login)
    monkeypatch.setattr(endpoints, "is_prod_mode", lambda: False)
    cliente = TestClient(endpoints.rotas_autenticacao)
    resposta = cliente.post(
        "/api/autenticacao/login",
        json={"email": "admin@example.test", "senha": "DemoAdmin-02!"},
    )
    cookie = cliente.cookies.get(endpoints.NOME_COOKIE_SESSAO)

    assert resposta.status_code == 200
    assert resposta.json()["sucesso"] is True
    assert "token" not in resposta.json()
    assert "DemoAdmin-02!" not in resposta.text
    assert cookie
    cabecalho_cookie = resposta.headers["set-cookie"].lower()
    assert "httponly" in cabecalho_cookie
    assert "samesite=strict" in cabecalho_cookie
    assert "secure" not in cabecalho_cookie
    digest = hashlib.sha256(cookie.encode("utf-8")).hexdigest()
    assert repositorio_com_seed_login.obter("sessoes", digest) is not None


def test_endpoint_usa_secure_em_producao_e_logout_remove_cookie(
    monkeypatch: pytest.MonkeyPatch,
    repositorio_com_seed_login: RepositorioMemoria,
) -> None:
    from starlette.testclient import TestClient

    import app.paginas.endpoints_autenticacao as endpoints

    monkeypatch.setattr(endpoints, "obter_repositorio", lambda: repositorio_com_seed_login)
    monkeypatch.setattr(endpoints, "is_prod_mode", lambda: True)
    cliente = TestClient(endpoints.rotas_autenticacao, base_url="https://testserver")
    login = cliente.post(
        "/api/autenticacao/login",
        json={"email": "recepcao@example.test", "senha": "DemoRecepcao-02!"},
    )
    assert "secure" in login.headers["set-cookie"].lower()
    assert endpoints.NOME_COOKIE_SESSAO in cliente.cookies

    logout = cliente.post("/api/autenticacao/logout")

    assert logout.status_code == 200
    assert logout.json() == {"sucesso": True, "mensagem": "Sessão encerrada."}
    assert endpoints.NOME_COOKIE_SESSAO not in cliente.cookies
    assert repositorio_com_seed_login.listar("sessoes") == []


def test_endpoint_sessao_sem_cookie_nao_autentica(
    monkeypatch: pytest.MonkeyPatch,
    repositorio_com_seed_login: RepositorioMemoria,
) -> None:
    from starlette.testclient import TestClient

    import app.paginas.endpoints_autenticacao as endpoints

    monkeypatch.setattr(endpoints, "obter_repositorio", lambda: repositorio_com_seed_login)
    cliente = TestClient(endpoints.rotas_autenticacao)

    resposta = cliente.get("/api/autenticacao/sessao")

    assert resposta.status_code == 200
    assert resposta.json()["sucesso"] is False
    assert resposta.json()["usuario_id"] is None
    assert resposta.json()["perfil"] is None


def test_guard_redireciona_sem_sessao_e_mantem_login_publico(
    monkeypatch: pytest.MonkeyPatch,
    repositorio_com_seed_login: RepositorioMemoria,
) -> None:
    from starlette.applications import Starlette
    from starlette.requests import Request
    from starlette.responses import PlainTextResponse
    from starlette.routing import Route
    from starlette.testclient import TestClient

    import app.paginas.endpoints_autenticacao as endpoints

    monkeypatch.setattr(endpoints, "obter_repositorio", lambda: repositorio_com_seed_login)

    async def pagina_interna(_: Request) -> PlainTextResponse:
        return PlainTextResponse("conteudo interno")

    async def pagina_login(_: Request) -> PlainTextResponse:
        return PlainTextResponse("login publico")

    async def rota_api(_: Request) -> PlainTextResponse:
        return PlainTextResponse("api publica")

    async def folha_estilo(_: Request) -> PlainTextResponse:
        return PlainTextResponse("input[name=\"email\"] { color: #111827; }")

    aplicacao = Starlette(
        routes=[
            Route("/", pagina_interna),
            Route("/login", pagina_login),
            Route("/login.css", folha_estilo),
            Route("/api/ping", rota_api),
        ]
    )
    cliente = TestClient(endpoints.proteger_paginas(aplicacao))

    raiz = cliente.get("/", follow_redirects=False)
    login_publico = cliente.get("/login")
    api_publica = cliente.get("/api/ping")
    css_publico = cliente.get("/login.css")

    assert raiz.status_code == 303
    assert raiz.headers["location"] == "/login"
    assert "conteudo interno" not in raiz.text
    assert login_publico.text == "login publico"
    assert api_publica.text == "api publica"
    assert css_publico.status_code == 200
    assert "#111827" in css_publico.text


def test_guard_permite_sessao_valida(
    monkeypatch: pytest.MonkeyPatch,
    repositorio_com_seed_login: RepositorioMemoria,
) -> None:
    import hashlib
    import secrets
    from datetime import datetime, timezone

    from starlette.applications import Starlette
    from starlette.requests import Request
    from starlette.responses import PlainTextResponse
    from starlette.routing import Route
    from starlette.testclient import TestClient

    import app.paginas.endpoints_autenticacao as endpoints
    from app.dominio.modelos import PerfilUsuario, SessaoAutenticada, Usuario

    monkeypatch.setattr(endpoints, "obter_repositorio", lambda: repositorio_com_seed_login)
    usuario = Usuario("usuario-guard-valido", "Pessoa Fictícia", PerfilUsuario.MEDICO)
    repositorio_com_seed_login.criar("usuarios", usuario)
    agora = datetime.now(timezone.utc)
    token = secrets.token_urlsafe(24)
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    repositorio_com_seed_login.criar_sessao(
        SessaoAutenticada(digest, usuario.id, agora, agora)
    )

    async def pagina_interna(_: Request) -> PlainTextResponse:
        return PlainTextResponse("conteudo autenticado")

    cliente = TestClient(
        endpoints.proteger_paginas(
            Starlette(routes=[Route("/", pagina_interna)])
        )
    )
    cliente.cookies.set(endpoints.NOME_COOKIE_SESSAO, token)

    resposta = cliente.get("/", follow_redirects=False)

    assert resposta.status_code == 200
    assert resposta.text == "conteudo autenticado"


def test_guard_redireciona_sessao_expirada_e_apaga_cookie(
    monkeypatch: pytest.MonkeyPatch,
    repositorio_com_seed_login: RepositorioMemoria,
) -> None:
    import hashlib
    import secrets
    from datetime import datetime, timedelta, timezone

    from starlette.applications import Starlette
    from starlette.requests import Request
    from starlette.responses import PlainTextResponse
    from starlette.routing import Route
    from starlette.testclient import TestClient

    import app.paginas.endpoints_autenticacao as endpoints
    from app.dominio.modelos import PerfilUsuario, SessaoAutenticada, Usuario

    monkeypatch.setattr(endpoints, "obter_repositorio", lambda: repositorio_com_seed_login)
    usuario = Usuario("usuario-guard", "Pessoa Fictícia", PerfilUsuario.ADMIN)
    repositorio_com_seed_login.criar("usuarios", usuario)
    agora = datetime.now(timezone.utc)
    token = secrets.token_urlsafe(24)
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    repositorio_com_seed_login.criar_sessao(
        SessaoAutenticada(
            digest,
            usuario.id,
            agora - timedelta(minutes=31),
            agora - timedelta(minutes=31),
        )
    )

    async def pagina_interna(_: Request) -> PlainTextResponse:
        return PlainTextResponse("conteudo interno")

    cliente = TestClient(
        endpoints.proteger_paginas(
            Starlette(routes=[Route("/", pagina_interna)])
        )
    )
    cliente.cookies.set(endpoints.NOME_COOKIE_SESSAO, token)

    resposta = cliente.get("/", follow_redirects=False)

    assert resposta.status_code == 303
    assert resposta.headers["location"] == "/login?sessao=expirada"
    assert "max-age=0" in resposta.headers["set-cookie"].lower()
    assert repositorio_com_seed_login.listar("sessoes") == []