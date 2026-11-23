# Spec Delta

## Purpose

Define destinos, permissões e respostas de acesso para cada perfil, mantendo as rotas e operações protegidas pela identidade autenticada.

## ADDED Requirements

### Requirement: Cada perfil possui uma rota inicial definida
O sistema SHALL encaminhar cada perfil para sua rota inicial: `recepcao` para `/recepcao`, `medico` para `/medico`, `paciente` para `/paciente` e `admin` para `/admin`.

#### Scenario: Destino inicial de recepção
- **WHEN** a rota inicial é solicitada por uma sessão válida de `recepcao`
- **THEN** o sistema encaminha a sessão para `/recepcao`

#### Scenario: Destino inicial de médico
- **WHEN** a rota inicial é solicitada por uma sessão válida de `medico`
- **THEN** o sistema encaminha a sessão para `/medico`

#### Scenario: Destino inicial de paciente
- **WHEN** a rota inicial é solicitada por uma sessão válida de `paciente`
- **THEN** o sistema encaminha a sessão para `/paciente`

#### Scenario: Destino inicial de administração
- **WHEN** a rota inicial é solicitada por uma sessão válida de `admin`
- **THEN** o sistema encaminha a sessão para `/admin`

### Requirement: A raiz encaminha conforme a sessão
A rota `/` SHALL encaminhar usuários sem sessão válida para `/login` e usuários autenticados para a rota inicial de seu perfil.

#### Scenario: Visitante acessa a raiz
- **WHEN** uma solicitação sem sessão válida acessa `/`
- **THEN** o sistema redireciona para `/login`

#### Scenario: Usuário autenticado acessa a raiz
- **WHEN** uma solicitação com sessão válida acessa `/`
- **THEN** o sistema redireciona para a rota inicial associada ao perfil da sessão

### Requirement: Acesso às rotas segue a matriz de perfis
O sistema SHALL permitir `/recepcao` somente a `recepcao`, `/medico` somente a `medico`, `/paciente` somente a `paciente`, `/admin` somente a `admin` e `/perfil` a `recepcao`, `medico` e `admin`.

#### Scenario: Perfil permitido acessa sua rota
- **WHEN** uma sessão válida solicita uma rota autorizada para seu perfil
- **THEN** o sistema apresenta a página da rota solicitada

#### Scenario: Perfil não permitido solicita rota protegida
- **WHEN** uma sessão válida solicita uma rota não autorizada para seu perfil
- **THEN** o sistema nega o acesso e apresenta a resposta 403

### Requirement: Rotas protegidas exigem sessão válida
O sistema SHALL exigir uma sessão válida nas rotas de perfil e em `/perfil` antes de apresentar seu conteúdo.

#### Scenario: Sessão ausente solicita rota protegida
- **WHEN** uma solicitação sem sessão válida acessa uma rota protegida
- **THEN** o sistema redireciona para `/login` e conserva a rota solicitada como destino candidato pós-login

#### Scenario: Sessão expirada solicita rota protegida
- **WHEN** uma sessão expirada solicita uma rota protegida
- **THEN** o sistema não apresenta o conteúdo e redireciona para `/login`

### Requirement: Destino pós-login é local e autorizado
O sistema SHALL aceitar `next` somente quando for um caminho local permitido ao perfil autenticado e SHALL usar a rota inicial do perfil nos demais casos.

#### Scenario: Destino local permitido
- **WHEN** `next` identifica uma rota local autorizada para o perfil autenticado
- **THEN** o sistema redireciona para essa rota após o login

#### Scenario: Destino externo ou malformado
- **WHEN** `next` contém uma URL externa ou não representa um caminho local válido
- **THEN** o sistema ignora o destino e redireciona para a rota inicial do perfil

#### Scenario: Destino local não autorizado
- **WHEN** `next` identifica uma rota local não permitida para o perfil autenticado
- **THEN** o sistema ignora o destino e redireciona para a rota inicial do perfil

### Requirement: Navegação mostra somente opções autorizadas
A navegação SHALL apresentar somente links para rotas permitidas ao perfil da sessão válida.

#### Scenario: Menu de recepção
- **WHEN** a navegação é apresentada a `recepcao`
- **THEN** ela oferece `/recepcao` e `/perfil` e não oferece rotas de outros perfis

#### Scenario: Menu de médico
- **WHEN** a navegação é apresentada a `medico`
- **THEN** ela oferece `/medico` e `/perfil` e não oferece rotas de outros perfis

#### Scenario: Menu de paciente
- **WHEN** a navegação é apresentada a `paciente`
- **THEN** ela oferece `/paciente` e não oferece rotas de outros perfis

#### Scenario: Menu de administração
- **WHEN** a navegação é apresentada a `admin`
- **THEN** ela oferece `/admin` e `/perfil` e não oferece rotas de outros perfis

### Requirement: Operações de serviço validam o perfil
O sistema SHALL verificar a permissão do perfil no limite da operação de serviço, inclusive quando a operação não é chamada pela interface.

#### Scenario: Chamada direta sem permissão
- **WHEN** uma operação de serviço é invocada por uma identidade sem o perfil exigido
- **THEN** o sistema lança `PermissionError` e não aplica a operação

### Requirement: Negações de autorização são auditadas sem segredos
O sistema SHALL registrar a identidade, a operação e o resultado de uma negação de autorização sem registrar senha, token de sessão ou hash de token.

#### Scenario: Registrar operação negada
- **WHEN** uma operação de serviço é negada por falta de permissão
- **THEN** o registro de auditoria identifica o ator e a operação negada e não contém credenciais nem tokens

### Requirement: Acesso negado tem página própria
O sistema SHALL apresentar uma página 403 em português quando uma sessão válida não tiver permissão para a rota solicitada.

#### Scenario: Apresentar acesso negado
- **WHEN** o sistema nega uma rota a uma sessão válida
- **THEN** apresenta a página 403 sem revelar conteúdo da rota protegida

### Requirement: Rota inexistente tem resposta própria
O sistema SHALL apresentar uma página 404 em português para caminhos não registrados.

#### Scenario: Solicitar caminho inexistente
- **WHEN** um usuário solicita um caminho que não corresponde a uma rota registrada
- **THEN** o sistema apresenta a página 404

### Requirement: Páginas e navegação permanecem utilizáveis em telas estreitas
As páginas de perfil e as respostas 403 e 404 SHALL permanecer legíveis e operáveis em viewport de aproximadamente 360 pixels e em viewport de notebook.

#### Scenario: Apresentar páginas em viewport estreita
- **WHEN** uma página de perfil ou erro é apresentada em viewport de aproximadamente 360 pixels
- **THEN** conteúdo e navegação permanecem utilizáveis sem sobreposição ou rolagem horizontal involuntária

#### Scenario: Apresentar páginas em viewport de notebook
- **WHEN** uma página de perfil ou erro é apresentada em viewport de notebook
- **THEN** conteúdo e navegação permanecem legíveis e organizados