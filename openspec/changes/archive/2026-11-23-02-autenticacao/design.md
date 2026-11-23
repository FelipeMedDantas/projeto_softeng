# Design

## Context

See [proposal.md](proposal.md) for motivation and scope. A fundação atual tem `Usuario.ativo`, mas não tem e-mail ou hash de senha; os parâmetros atendem apenas às regras da fila; o repositório em memória já protege operações com `RLock`. A capability principal de autenticação ainda não existe.

## Goals / Non-Goals

**Goals:**
- Adicionar autenticação de equipe sem dependência externa e sem colocar segredos no estado compartilhado ou nos logs.
- Garantir atualizações atômicas de tentativas, sessões e auditoria no repositório central.
- Permitir testes determinísticos de bloqueio e inatividade por injeção de horário.
- Manter a interface Reflex responsiva e limitada à apresentação e coordenação.

**Non-Goals:**
- Implementar o mapa completo de autorização por recurso e páginas 403/404; essas decisões pertencem à Change 03.
- Recuperar ou trocar senha, exibir páginas 403/404 ou autenticar pacientes.
- Persistir sessão ou usuário entre reinicializações e processos.

## Decisions

### Modelo de usuário e credenciais

- Estender `Usuario` com e-mail normalizado e `senha_hash`; `ativo` já existe. Não adicionar campo de senha em texto puro.
- Codificar o hash como um valor autocontido contendo versão/algoritmo, custo, salt e digest, para que o repositório de usuários armazene somente `senha_hash` e a verificação permaneça reproduzível.
- Usar `hashlib.pbkdf2_hmac` com SHA-256, salt criptograficamente aleatório de 16 bytes e `hmac.compare_digest`. `iteracoes_hash_senha` será configurável, padrão 600000 e validado como inteiro maior que zero.
- Alternativa considerada: hash rápido sem salt ou biblioteca externa. Rejeitada por ser inadequado para senha ou desnecessária, respectivamente.

### Seed e contas de demonstração

- Manter três contas fictícias de equipe: `admin@example.test` / `DemoAdmin-02!`, `recepcao@example.test` / `DemoRecepcao-02!` e `medico@example.test` / `DemoMedico-02!`. O README documentará essas senhas exclusivas de demonstração local, com aviso explícito para nunca reutilizá-las fora do seed.
- O seed receberá as senhas de demonstração como entrada transitória, derivará um salt novo e persistirá somente o hash. Uma nova carga não sobrescreverá usuários já existentes; reset do repositório recria as contas.
- `obter_repositorio()` fará bootstrap idempotente do seed uma vez, de forma segura entre threads; `app.py` solicitará o repositório no startup. O seed chamará o mesmo helper de hash usado na autenticação.
- E-mails de acesso serão únicos após `.strip().lower()` no modelo, seed e serviço. Não incluir e-mails, senhas ou hashes de senha nos detalhes de auditoria.

### Configuração e tentativas

- Acrescentar ao objeto de parâmetros `tempo_sessao_min=30`, `max_tentativas_login=5` e `tempo_bloqueio_min=5`, todos positivos. Acrescentar `iteracoes_hash_senha=600000` para não fixar no serviço o custo computacional do hash.
- Armazenar tentativas por e-mail normalizado e fazer leitura/verificação de bloqueio e atualização de contador sob operações atômicas do repositório. Enquanto bloqueado, não executar a verificação de senha e apresentar tempo restante arredondado para cima em minutos.
- Ao completar o prazo de bloqueio, zerar a sequência e aceitar nova tentativa; login válido também zera o contador. Credenciais inválidas sempre retornam a mesma mensagem exata, independentemente de o e-mail existir.
- Verificar senha correta antes de apresentar a mensagem de conta desativada, reduzindo enumeração de contas; ainda assim, a conta inativa nunca recebe sessão.
- Alternativa considerada: manter contadores em `rx.State` ou incrementá-los sem transação. Rejeitada porque estado é por navegador e concorrência poderia contornar o limite.

### Sessões e transporte do token

- Gerar token opaco imprevisível com `secrets.token_urlsafe`; enviar o valor apenas em cookie de resposta `HttpOnly`, `SameSite=Strict`, com `Secure` em produção e escopo limitado à aplicação.
- Guardar no repositório somente o hash SHA-256 do token, identidade, criação e última atividade. O token bruto não entra em `rx.State`, logs, auditoria ou banco de dados em memória.
- Reflex `rx.Cookie` é client-side e acessível por JavaScript; não será usado para o token. Usar endpoints server-side adicionados pelo `api_transformer` (Starlette/FastAPI já disponível no stack) para login, consulta/renovação da sessão e logout, com `Set-Cookie`/remoção de cookie. A tela usa esses endpoints sem renderizar credenciais ou token.
- Validar a sessão em cada operação de autenticação; atividade válida atualiza `ultima_atividade`. Inatividade igual ou superior ao limite remove a sessão e informa a expiração. O serviço aceita `agora` como instante UTC opcional, usando relógio UTC atual quando omitido.
- Logout invalida no repositório o digest apresentado, envia cookie expirado e redireciona a `/login`; voltar no histórico não restaura a identidade.
- Alternativa considerada: manter token em variável pública Reflex ou `localStorage`. Rejeitada porque código cliente pode lê-lo e exfiltrá-lo.

### Operações do repositório e auditoria

- Centralizar coleções de tentativas, sessões e `RegistroAuditoria` em `app/dados/repositorio.py`. Expor operações com lock que combinem decisão e gravação (por exemplo, registrar falha/estabelecer bloqueio; consumir sessão/renovar atividade; invalidar sessão e registrar evento).
- O serviço não manipula coleções privadas nem contadores globais; calcula hash/verifica senha fora de seções críticas quando possível e confirma mudanças sob lock.
- Auditar `login_sucesso`, `login_falhou`, `login_bloqueado` e `logout`; gravar apenas instante, identificador do usuário quando conhecido e categoria do evento. Para e-mail desconhecido, usar ator genérico sem guardar o e-mail nos detalhes.
- Nunca registrar senha submetida, senha em texto puro, `senha_hash`, token bruto ou digest de sessão em auditoria ou mensagens. Filtrar os corpos dos endpoints dos logs de requisição.

### Interface e destino pós-login

- A tela `/login` usará formulário com e-mail e senha mascarada, ação de mostrar/ocultar senha e submissão por Enter. O controle de visibilidade será apenas estado da interface.
- O cabeçalho mostrará perfil autenticado e botão `Sair`; confirmação de identidade e sessão virá do endpoint/repositório, não de um perfil escolhido visualmente.
- A raiz e páginas internas que usam `layout_base` serão protegidas por `EstadoLayout.verificar_sessao` no carregamento e manterão o conteúdo oculto enquanto a sessão não for confirmada. A tela `/login` é pública e não usa o guard.
- Como ainda só existe `/`, todos os perfis de equipe serão direcionados para essa rota após login. A Change 03 introduzirá o mapa completo de autorização e as páginas 403/404; até lá, não se presume autorização por perfil em cada recurso.
- Validar a página em aproximadamente 360 px e em viewport de notebook. `app/app.py` mantém `html_lang="pt-BR"`; mensagens orientam em português, incluindo `Sua sessão expirou. Entre novamente.`.

### Contraste dos controles de login

- Definir explicitamente fundo, texto, placeholder, borda e foco dos inputs; definir fundo/texto contrastantes nos botões, em vez de depender do modo de cor do navegador.
- Alternativa considerada: depender do tema e do modo escuro do sistema operacional. Rejeitada porque a tela precisa ter a mesma legibilidade em ambientes diferentes.

## Risks / Trade-offs

- [Sessões são apenas em memória e se perdem no restart ou em workers diferentes] → manter implantação de processo único nesta etapa e exigir login novamente após reinício.
- [Credenciais de demonstração publicadas no README podem ser reutilizadas] → usar domínios `.test`, avisar que são exclusivamente locais e não usar essas contas em produção.
- [Uma conta bloqueada pode ser usada para negar serviço ao seu titular] → prazo curto parametrizado, resposta genérica de credenciais inválidas e mensagem de bloqueio apenas no período necessário; mecanismo de recuperação fica para change futura.
- [Mapa completo de rotas ainda não existe] → não expor nesta etapa conteúdo real ou ações protegidas em rotas sem guard; documentar que autenticação de sessão não substitui autorização, que será implementada na Change 03.
- [Custo PBKDF2 afeta latência de login] → torná-lo configurável e medir no ambiente de execução, sem reduzir silenciosamente o padrão por conveniência.

## Migration Plan

1. Acrescentar e validar parâmetros, campos de usuário e primitivas de hash sem alterar a separação de camadas.
2. Adicionar operações atômicas para tentativas, sessões e auditoria ao repositório; atualizar seed fictício e documentação das credenciais locais.
3. Implementar endpoints server-side com cookie protegido e integrar a página de login e a ação de logout ao layout.
4. Testar serviços com relógio injetado, executar a suíte pytest e validar a interface em celular/notebook.
5. Não há migração persistente: usuários e sessões existem apenas em memória; reinicialização recria o seed com hashes novos e invalida todas as sessões.