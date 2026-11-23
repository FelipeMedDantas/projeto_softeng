# Spec Delta

## Purpose

Permitir que a equipe entre e saia do Sistema de Priorização de Atendimento com credenciais verificadas, tentativas limitadas, sessões temporárias e auditoria sem segredos, mantendo os dados de autenticação em memória.

## ADDED Requirements

**Parâmetros de Segurança**

### Requirement: Limites de autenticação são configuráveis
O sistema SHALL disponibilizar duração da sessão, máximo de tentativas, duração do bloqueio e custo de hash como parâmetros configuráveis com os padrões definidos para esta change.

#### Scenario: Consultar parâmetros padrão de autenticação
- **WHEN** os parâmetros são carregados pela primeira vez ou restaurados
- **THEN** `tempo_sessao_min` é 30, `max_tentativas_login` é 5, `tempo_bloqueio_min` é 5 e `iteracoes_hash_senha` é 600000

### Requirement: Parâmetros de autenticação rejeitam valores inválidos
O sistema SHALL recusar qualquer parâmetro de autenticação cujo valor seja menor ou igual a zero, preservando a configuração anterior e apresentando mensagem clara em português.

#### Scenario: Rejeitar duração ou limite inválido
- **WHEN** qualquer parâmetro de autenticação é configurado com valor menor ou igual a zero
- **THEN** a alteração é recusada, a configuração anterior permanece e a mensagem informa que o valor deve ser maior que zero

**Credenciais e Autenticação da Equipe**

### Requirement: Login atende somente perfis de equipe
O sistema SHALL autenticar por e-mail e senha os perfis `admin`, `recepcao` e `medico`, sem usar o fluxo de identificação de paciente.

#### Scenario: Autenticar integrante da equipe
- **WHEN** um usuário de equipe fornece e-mail e senha válidos e está ativo
- **THEN** a identidade e o perfil corretos são aceitos para criação de sessão

#### Scenario: Não aceitar perfil de paciente neste fluxo
- **WHEN** uma tentativa de autenticação usa o perfil `paciente`
- **THEN** o fluxo de equipe não autentica o paciente nem solicita CPF ou número de paciente

### Requirement: Senhas são verificadas por hash com salt
O sistema SHALL verificar senhas por meio de hash derivado com salt aleatório individual, sem armazenar a senha em texto puro nos registros de usuário.

#### Scenario: Armazenar e verificar senha
- **WHEN** uma senha de seed é preparada para autenticação
- **THEN** o usuário armazena somente `senha_hash`, que permite verificar a senha usando salt e custo configurado, sem guardar a senha original

#### Scenario: Usar salt distinto por usuário
- **WHEN** duas contas recebem a mesma senha de demonstração
- **THEN** seus valores `senha_hash` são diferentes por usarem salts aleatórios distintos

### Requirement: E-mail é normalizado igualmente em cadastro e login
O sistema SHALL remover espaços externos e converter e-mails para minúsculas antes de armazená-los, compará-los ou autenticar.

#### Scenario: Autenticar e-mail com espaços e letras maiúsculas
- **WHEN** um usuário fornece um e-mail com espaços externos ou letras maiúsculas
- **THEN** o e-mail normalizado corresponde à mesma conta cadastrada

### Requirement: Seed está disponível desde a inicialização do repositório
O sistema SHALL carregar idempotentemente as contas fictícias de equipe antes de o repositório global ser usado pela aplicação ou pelo serviço de autenticação.

#### Scenario: Obter repositório pela primeira vez
- **WHEN** a aplicação inicia ou o serviço solicita o repositório global ainda não inicializado
- **THEN** as três contas de equipe existem e podem autenticar com as credenciais de demonstração documentadas

### Requirement: Credenciais inválidas recebem erro genérico
O sistema SHALL responder com `E-mail ou senha incorretos.` tanto para e-mail inexistente quanto para senha incorreta.

#### Scenario: E-mail inexistente
- **WHEN** a tentativa usa um e-mail que não corresponde a usuário
- **THEN** a resposta é exatamente `E-mail ou senha incorretos.`

#### Scenario: Senha incorreta
- **WHEN** a tentativa usa e-mail conhecido e senha incorreta
- **THEN** a resposta é exatamente `E-mail ou senha incorretos.`

### Requirement: Conta desativada não inicia sessão
O sistema SHALL recusar uma conta desativada com mensagem clara em português e não criar sessão.

#### Scenario: Recusar conta desativada com credencial correspondente
- **WHEN** a senha corresponde a uma conta cujo atributo `ativo` é falso
- **THEN** o login é recusado com orientação para contatar a administração e nenhuma sessão é criada

**Tentativas e Bloqueio Temporário**

### Requirement: Falhas consecutivas provocam bloqueio temporário
O sistema SHALL bloquear novas tentativas para o identificador de login após `max_tentativas_login` falhas consecutivas, pelo período configurado em `tempo_bloqueio_min`.

#### Scenario: Atingir o máximo de tentativas
- **WHEN** a quinta falha consecutiva ocorre com os padrões ativos
- **THEN** novas tentativas para aquele identificador são temporariamente bloqueadas por cinco minutos

### Requirement: Bloqueio informa o tempo restante e termina automaticamente
Enquanto houver bloqueio, o sistema SHALL informar em português o tempo restante e SHALL permitir nova tentativa assim que o período configurado terminar.

#### Scenario: Consultar tentativa durante bloqueio
- **WHEN** uma tentativa ocorre antes do fim do bloqueio
- **THEN** a autenticação não é executada e a mensagem informa quanto tempo falta para tentar novamente

#### Scenario: Tentar novamente depois do bloqueio
- **WHEN** o relógio alcança ou ultrapassa o instante de liberação
- **THEN** o bloqueio termina e uma nova tentativa pode ser verificada

### Requirement: Autenticação válida zera falhas consecutivas
Após validar uma credencial ativa, o sistema SHALL zerar o contador de falhas consecutivas daquele identificador antes de criar a sessão.

#### Scenario: Reiniciar contador após login válido
- **WHEN** o usuário autentica com sucesso antes de atingir o bloqueio
- **THEN** o contador de tentativas consecutivas volta a zero

### Requirement: Operações de autenticação aceitam relógio de referência
As operações de login, validação de sessão e logout SHALL aceitar um instante opcional `agora` para tornar bloqueio e expiração determinísticos em testes.

#### Scenario: Testar bloqueio sem espera real
- **WHEN** um teste fornece instantes `agora` sucessivos às operações de autenticação
- **THEN** o bloqueio e sua liberação são determinados pelos instantes fornecidos, sem depender de espera real

**Sessões e Auditoria**

### Requirement: Login cria sessão temporária em memória
Após login válido, o sistema SHALL criar uma sessão associada à identidade autenticada, limitada pela duração de inatividade configurada.

#### Scenario: Criar sessão após login válido
- **WHEN** um usuário ativo fornece credenciais válidas
- **THEN** é criada uma sessão em memória associada ao usuário e ao instante de atividade

### Requirement: Inatividade expira sessão e retorna ao login
O sistema SHALL expirar a sessão quando a inatividade alcançar `tempo_sessao_min` e orientar o usuário a entrar novamente.

#### Scenario: Expirar sessão inativa
- **WHEN** a última atividade ocorreu há 30 minutos ou mais com os padrões ativos
- **THEN** a sessão é invalidada, o usuário é enviado a `/login` e vê `Sua sessão expirou. Entre novamente.`

#### Scenario: Renovar atividade dentro do prazo
- **WHEN** uma sessão válida é usada antes do limite de inatividade
- **THEN** seu instante de última atividade é atualizado

### Requirement: Logout invalida definitivamente a sessão
O sistema SHALL remover ou invalidar a sessão no repositório durante logout e encaminhar o usuário para `/login`.

#### Scenario: Encerrar sessão
- **WHEN** um usuário solicita sair
- **THEN** a sessão deixa de ser válida e a navegação é encaminhada para `/login`

#### Scenario: Voltar no navegador após logout
- **WHEN** o usuário retorna pelo histórico do navegador após logout
- **THEN** a sessão encerrada não é reaberta nem aceita como autenticada

### Requirement: Estado de sessão, tentativas e auditoria fica no repositório central
O sistema SHALL ler e alterar sessões, tentativas e registros de auditoria exclusivamente pelo repositório compartilhado protegido contra concorrência.

#### Scenario: Atualizar estado de autenticação concorrente
- **WHEN** operações de sessão, tentativas ou auditoria ocorrem simultaneamente
- **THEN** o repositório mantém as atualizações consistentes sob lock, sem usar `rx.State` como armazenamento compartilhado

### Requirement: Auditoria registra eventos sem segredos
O sistema SHALL auditar login bem-sucedido, falha, bloqueio e logout sem registrar senhas, hashes de sessão ou tokens em auditoria, tela ou logs.

#### Scenario: Auditar sucesso, falha, bloqueio e logout
- **WHEN** cada um desses eventos ocorre
- **THEN** um registro de auditoria identifica o tipo do evento e o instante sem conter senha, `senha_hash` ou token de sessão

**Interface de Login e Logout**

### Requirement: Página de login oferece entrada segura
A interface SHALL oferecer em `/login` campos de e-mail e senha, envio por Enter e controle para mostrar ou ocultar a senha.

#### Scenario: Enviar credenciais pelo formulário
- **WHEN** o usuário preenche e-mail e senha e pressiona Enter
- **THEN** o formulário executa o login sem exibir a senha em texto enquanto a opção de mostrar senha está desativada

#### Scenario: Alternar visibilidade da senha
- **WHEN** o usuário aciona o controle de mostrar ou ocultar senha
- **THEN** o campo alterna entre os tipos senha e texto sem alterar o valor digitado

### Requirement: Login usa idioma e mensagens do projeto
A tela de autenticação SHALL usar `html_lang="pt-BR"` e mensagens curtas em português que indiquem a ação necessária.

#### Scenario: Apresentar orientação ao usuário
- **WHEN** login, bloqueio, conta desativada ou expiração exigem ação do usuário
- **THEN** a interface apresenta orientação curta em português sobre o próximo passo

### Requirement: Destino pós-login respeita o perfil disponível
Após autenticação válida, o sistema SHALL encaminhar o usuário à rota inicial definida para seu perfil.

#### Scenario: Redirecionar perfis sem página própria
- **WHEN** qualquer perfil de equipe autentica enquanto ainda não há páginas iniciais específicas
- **THEN** o usuário é encaminhado à rota comum `/`

### Requirement: Layout apresenta ação de logout
O layout da área de equipe SHALL apresentar o botão `Sair`, que encerra a sessão e redireciona para `/login`.

#### Scenario: Sair pelo cabeçalho
- **WHEN** o usuário autenticado aciona `Sair`
- **THEN** a sessão é invalidada e a tela de login é apresentada

### Requirement: Login adapta-se a celular e notebook
A página de login SHALL permanecer utilizável em largura de aproximadamente 360 pixels e em viewport de notebook, sem sobreposição ou rolagem horizontal involuntária.

#### Scenario: Usar login em celular
- **WHEN** a tela é exibida em viewport de aproximadamente 360 pixels
- **THEN** campos, controle de senha e envio permanecem visíveis e operáveis sem rolagem horizontal

#### Scenario: Usar login em notebook
- **WHEN** a tela é exibida em viewport de notebook
- **THEN** campos, controle de senha e envio permanecem organizados e operáveis

### Requirement: Controles de login têm contraste legível
Os campos de e-mail e senha SHALL usar fundo branco, texto escuro, placeholder cinza legível e borda definida com foco visível; os botões SHALL manter contraste alto.

#### Scenario: Exibir campos e botões em celular ou notebook
- **WHEN** a tela de login é renderizada em celular ou notebook
- **THEN** os campos usam fundo `#FFFFFF`, texto `#111827`, placeholder `#6B7280`, borda `#9CA3AF` com foco visível e botões com texto/fundo de alto contraste

### Requirement: Raiz e páginas internas protegidas exigem sessão válida
A rota raiz e as páginas internas que usam o layout protegido SHALL ocultar conteúdo e redirecionar ao login quando não houver sessão válida.

#### Scenario: Acessar a raiz sem sessão
- **WHEN** uma pessoa sem sessão válida acessa `/`
- **THEN** o conteúdo do sistema não é exibido e a navegação redireciona para `/login`

#### Scenario: Acessar página interna protegida sem sessão
- **WHEN** uma pessoa sem sessão válida acessa uma página interna registrada com o layout protegido
- **THEN** o conteúdo da página não é exibido e a navegação redireciona para `/login`

#### Scenario: Acessar área protegida com sessão válida
- **WHEN** uma pessoa com sessão válida acessa `/` ou página interna protegida
- **THEN** o conteúdo permitido ao perfil autenticado é apresentado