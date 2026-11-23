# base-projeto Specification

## Purpose

Define a fundação do Sistema de Priorização de Atendimento em uma capability coesa, cobrindo modelos de domínio, parâmetros de negócio, estado fictício em memória e interface Reflex sem incluir os fluxos operacionais posteriores.

## Requirements

**Fundação de Domínio**

### Requirement: Modelos do domínio representam as entidades base
O domínio SHALL disponibilizar modelos tipados para usuário, paciente, sintoma, atendimento e registro de auditoria, incluindo seus dados essenciais.

#### Scenario: Consumir os modelos base
- **WHEN** um serviço ou teste importa os modelos do domínio
- **THEN** encontra representações para Usuario, Paciente, Sintoma, Atendimento e RegistroAuditoria

### Requirement: Perfis de usuário possuem valores estáveis
O domínio SHALL representar os perfis `recepcao`, `medico`, `paciente` e `admin` como valores distintos e estáveis.

#### Scenario: Reconhecer todos os perfis
- **WHEN** os perfis disponíveis são consultados
- **THEN** são retornados exatamente `recepcao`, `medico`, `paciente` e `admin`

### Requirement: Status de atendimento possuem valores estáveis
O domínio SHALL representar os estados `aguardando`, `em_atendimento`, `finalizado`, `cancelado` e `nao_compareceu` como valores distintos.

#### Scenario: Reconhecer todos os estados
- **WHEN** os status disponíveis são consultados
- **THEN** são retornados exatamente `aguardando`, `em_atendimento`, `finalizado`, `cancelado` e `nao_compareceu`

### Requirement: Pacote de domínio é independente da interface
O pacote de domínio SHALL ser importável e testável sem importar ou inicializar Reflex.

#### Scenario: Importar domínio sem Reflex
- **WHEN** módulos do domínio são importados em um ambiente sem Reflex disponível
- **THEN** os modelos e parâmetros do domínio podem ser carregados sem erro causado por dependência da interface

**Parametrização Configurável**

### Requirement: Parâmetros de priorização possuem padrões conhecidos
O sistema SHALL disponibilizar os padrões de gravidade, prioridade legal, bônus de espera, limites de cor e capacidade de fila definidos para o projeto.

#### Scenario: Consultar parâmetros padrão
- **WHEN** a configuração é restaurada ou carregada pela primeira vez
- **THEN** modo de gravidade é `maior`, idade de idoso é 60, idade de criança é 12, pontos legais são 1, intervalo de bônus é 30 minutos, teto de bônus é 7, limite alto é 8, limite médio é 5 e capacidade é 30

### Requirement: Modo de gravidade é selecionável
O sistema SHALL aceitar somente os modos de gravidade `maior`, `soma` e `media` como valores configuráveis.

#### Scenario: Rejeitar modo de gravidade desconhecido
- **WHEN** um modo fora de `maior`, `soma` ou `media` é solicitado
- **THEN** a alteração é recusada com mensagem clara em português e a configuração anterior permanece inalterada

### Requirement: Alterações de parâmetros são validadas
O sistema SHALL recusar parâmetros fora dos domínios válidos, incluindo intervalo de bônus menor ou igual a zero, capacidade menor que um e limite alto menor que limite médio.

#### Scenario: Recusar intervalo de bônus inválido
- **WHEN** o intervalo de bônus é alterado para zero ou valor negativo
- **THEN** a alteração é recusada com mensagem clara em português e o valor anterior permanece

#### Scenario: Recusar capacidade inválida
- **WHEN** a capacidade de fila é alterada para valor menor que um
- **THEN** a alteração é recusada com mensagem clara em português e o valor anterior permanece

#### Scenario: Recusar limites de cor inconsistentes
- **WHEN** o limite alto é definido abaixo do limite médio
- **THEN** a alteração é recusada com mensagem clara em português e os limites anteriores permanecem

### Requirement: Parâmetros podem ser restaurados
O sistema SHALL permitir restaurar todos os parâmetros aos padrões do projeto em uma única operação.

#### Scenario: Restaurar configuração padrão
- **WHEN** a operação de restauração é solicitada
- **THEN** todos os parâmetros retornam aos seus valores padrão documentados

### Requirement: Regras de pontuação permanecem parametrizadas
Os parâmetros SHALL expressar gravidade por modo selecionado, prioridade legal não acumulável, bônus por intervalo de espera com teto e resultado final limitado ao intervalo de 1 a 10.

#### Scenario: Aplicar os parâmetros em uma implementação futura
- **WHEN** o motor de pontuação for implementado em change posterior
- **THEN** usará os parâmetros configurados, aplicará no máximo uma prioridade legal e limitará o resultado entre 1 e 10, sem introduzir constantes de negócio paralelas

**Persistência em Memória e Concorrência**

### Requirement: Dados compartilhados permanecem em memória
O armazenamento compartilhado SHALL existir somente em memória e não depender de banco externo, Xano ou persistência externa.

#### Scenario: Iniciar a aplicação sem armazenamento externo
- **WHEN** a aplicação é iniciada para esta change
- **THEN** os dados compartilhados são atendidos pelo repositório em memória, sem conexão a banco ou serviço externo

### Requirement: Operações do repositório são seguras entre threads
O repositório SHALL proteger as operações de criação, leitura, atualização, remoção e reinicialização do estado contra acesso concorrente.

#### Scenario: Executar gravações concorrentes
- **WHEN** múltiplas threads gravam registros simultaneamente
- **THEN** cada gravação concluída permanece acessível sem corromper o estado compartilhado

### Requirement: Estado inicial pode ser restaurado
O repositório SHALL oferecer uma operação para limpar e restaurar o estado inicial definido pelo seed.

#### Scenario: Reinicializar o estado
- **WHEN** a operação de reset é solicitada
- **THEN** os dados criados após a inicialização são removidos e o estado inicial é reconstituído

### Requirement: Seed contém somente dados fictícios
O seed SHALL criar um administrador, um recepcionista, um médico, dez sintomas com gravidades de 1 a 8 e seis pacientes com CPFs fictícios com dígitos verificadores matematicamente válidos.

#### Scenario: Carregar seed inicial
- **WHEN** o seed é carregado no estado vazio
- **THEN** existem as quantidades e entidades especificadas, todos os CPFs passam pela validação de dígitos e nenhum registro representa pessoa real

### Requirement: Carregar seed repetidamente não duplica registros
A inicialização do seed SHALL ser idempotente para o estado inicial, mantendo apenas um conjunto dos registros previstos.

#### Scenario: Repetir inicialização
- **WHEN** a rotina de seed é chamada mais de uma vez
- **THEN** as quantidades de usuários, sintomas e pacientes permanecem iguais às previstas, sem duplicação

**Interface Base Reflex**

### Requirement: Interface utiliza português brasileiro
A interface SHALL declarar `html_lang="pt-BR"` e apresentar conteúdo, comentários de interface e mensagens ao usuário em português.

#### Scenario: Carregar a página inicial
- **WHEN** a rota inicial é renderizada
- **THEN** o idioma do documento é `pt-BR` e os textos visíveis estão em português

### Requirement: Layout base adapta-se a celular e notebook
A interface SHALL apresentar cabeçalho, área de conteúdo e navegação-base legíveis em larguras de aproximadamente 360 pixels e em janela de notebook.

#### Scenario: Exibir layout em celular
- **WHEN** a interface é renderizada em janela de aproximadamente 360 pixels
- **THEN** cabeçalho, conteúdo e navegação continuam utilizáveis sem sobreposição ou rolagem horizontal causada pelo layout

#### Scenario: Exibir layout em notebook
- **WHEN** a interface é renderizada em janela de notebook
- **THEN** cabeçalho, navegação e área de conteúdo permanecem organizados e legíveis

### Requirement: Navegação-base identifica opções por perfil
A interface SHALL oferecer estrutura de menu capaz de apresentar rótulos correspondentes aos perfis recepção, médico, paciente e administrador, sem realizar autenticação ou controlar acesso nesta change.

#### Scenario: Apresentar navegação representativa por perfil
- **WHEN** a interface base é consultada para um perfil
- **THEN** apresenta a estrutura e os rótulos associados ao perfil sem afirmar que a identidade foi autenticada ou que a rota está protegida

### Requirement: Mensagens ao usuário são padronizadas
A interface SHALL disponibilizar um componente comum para exibir mensagens de sucesso, informação e erro em português.

#### Scenario: Exibir mensagem de erro
- **WHEN** um componente solicita a apresentação de uma mensagem de erro
- **THEN** a mensagem aparece no formato visual comum e em português

### Requirement: Faixa visual reflete os limites configurados
A interface SHALL classificar pontuações de 1 a 10 como vermelha a partir do limite alto, laranja a partir do limite médio e verde abaixo do limite médio.

#### Scenario: Exibir faixa vermelha
- **WHEN** uma pontuação é maior ou igual ao limite alto configurado
- **THEN** a faixa de cor é vermelha

#### Scenario: Exibir faixa laranja
- **WHEN** uma pontuação é menor que o limite alto e maior ou igual ao limite médio configurado
- **THEN** a faixa de cor é laranja

#### Scenario: Exibir faixa verde
- **WHEN** uma pontuação é menor que o limite médio configurado
- **THEN** a faixa de cor é verde

### Requirement: Estado de interface não é armazenamento compartilhado
O estado Reflex SHALL ser tratado como estado por sessão de navegador, e não como fonte de dados compartilhada entre sessões.

#### Scenario: Manter dados compartilhados fora do estado de sessão
- **WHEN** mais de uma sessão precisa acessar os mesmos registros em memória
- **THEN** os registros compartilhados são lidos e alterados pelo repositório comum, não por estado isolado de uma sessão Reflex