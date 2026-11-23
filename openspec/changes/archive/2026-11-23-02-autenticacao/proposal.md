# Proposal

## Why

A base do sistema já define perfis de equipe, mas ainda não verifica identidade nem controla sessões de equipe. Esta change acrescenta autenticação com credenciais fictícias de demonstração, proteção contra tentativas repetidas e encerramento/expiração de sessão, sem antecipar o mapa completo de autorização das páginas.

## What Changes

- Adicionar autenticação por e-mail e senha para os perfis de equipe `admin`, `recepcao` e `medico`, com mensagens em português e erro genérico para credenciais inválidas.
- Configurar duração da sessão, máximo de tentativas, duração do bloqueio e custo de hash; validar os limites antes de aplicá-los.
- Gerar hashes de senha com salt usando `hashlib.pbkdf2_hmac`; manter apenas hashes nos registros de usuário e não expor senhas ou tokens em auditoria, tela ou estado persistido.
- Centralizar tentativas, sessões e auditoria no repositório em memória, com operações atômicas protegidas por `RLock`.
- Criar login responsivo em `/login`, logout no cabeçalho, controle de sessão por inatividade e proteção de `/`/páginas internas com testes determinísticos e relógio injetável.
- Atualizar seed fictício e README com credenciais exclusivamente de demonstração.
- Manter fora do escopo recuperação/troca de senha, mapa completo de autorização e páginas 403/404 (Change 03) e login de paciente por CPF + número (Change 13).

## Capabilities

### New Capabilities
- `autenticacao`: autenticação de equipe, bloqueio temporário, sessões expiradas ou encerradas e registro seguro de auditoria.

### Modified Capabilities

Nenhuma. `base-projeto` permanece como contrato da fundação; esta change introduz a capacidade de autenticação separadamente.

## Impact

- Código previsto: `app/dominio/modelos.py`, `app/dominio/parametros.py`, `app/dados/repositorio.py`, `app/dados/seed.py`, `app/servicos/autenticacao.py`, `app/paginas/login.py`, `app/componentes/layout.py` e `app/app.py`.
- Testes: `tests/test_autenticacao.py`, incluindo tentativas, bloqueio, expiração, credenciais desativadas, hash/salt e logout.
- Documentação: `README.md` para credenciais de demonstração e limites de uso.
- Sem dependências externas: primitivas de hash e aleatoriedade vêm da biblioteca padrão; armazenamento segue apenas em memória.
- Rota inicial pós-login: `/` para todos os perfis enquanto páginas iniciais próprias não existirem; o mapa de proteção das demais rotas continua na Change 03.