# Design

## Context

See [proposal.md](proposal.md) for motivation and scope. O scaffold atual tem apenas uma página Reflex padrão, sem camadas de domínio, dados ou testes. O projeto já usa Python 3.11+, Reflex e pytest. Os contratos detalhados estão nas specs desta change.

## Goals / Non-Goals

**Goals:**
- Definir fronteiras de pacote que permitam testar regras e modelos sem carregar Reflex.
- Centralizar o estado compartilhado do processo e mantê-lo consistente entre threads.
- Fazer da configuração de negócio a única origem dos limites e valores usados pela interface-base.
- Deixar a página inicial executável com seed fictício e apresentar a base em português brasileiro.

**Non-Goals:**
- Garantir persistência entre reinicializações ou entre múltiplos processos/servidores.
- Implementar autenticação, autorização de rotas, cálculo de pontuação, ordenação de fila ou fluxos clínicos.
- Integrar dados, serviços ou sistemas de saúde reais.

## Decisions

### Fronteiras de pacote

- `app/dominio/` conterá `modelos.py` e `parametros.py`, sem imports de Reflex. Os modelos serão dataclasses e enums para entidades, perfis e status.
- `app/dados/` conterá `repositorio.py` e `seed.py`; `app/servicos/` poderá coordenar operações Python puras sem importar componentes de interface.
- `app/paginas/` e `app/componentes/` conterão a apresentação Reflex. `app/app.py` registrará a página inicial e configurará o idioma do documento.
- Alternativa considerada: manter todos os módulos em `app/app.py`, como no scaffold atual. Rejeitada porque mistura regras, dados e apresentação e torna o domínio dependente do runtime Reflex.

### Armazenamento compartilhado em memória

- O repositório será uma instância única no processo, protegida por `threading.RLock`; suas operações de leitura e escrita manterão o lock durante o acesso às coleções.
- O estado compartilhado de negócio não será mantido em `rx.State`, que permanece por sessão de navegador. Estado compartilhado entre processos não será prometido.
- A API será genérica o bastante para CRUD das entidades do domínio, e um reset devolverá o repositório ao conjunto produzido pelo seed.
- Alternativa considerada: banco local ou serviço externo. Rejeitada nesta change para manter o requisito apenas em memória e eliminar dependências de infraestrutura.

### Configuração de negócio

- `parametros.py` será a origem dos padrões e exporá leitura, atualização validada e restauração. Atualizações inválidas falharão em português e não alterarão parcialmente o estado.
- Os padrões são: modo `maior` (alternativas `soma`, `media`), idade de idoso 60, idade de criança 12, pontos legais 1 sem acumular, intervalo de bônus 30 minutos, teto de bônus 7, limite alto 8, limite médio 5 e capacidade 30.
- O contrato de pontuação futura é gravidade conforme o modo + prioridade legal + bônus de espera por intervalo limitado pelo teto; o resultado será limitado a 1–10. Esta change apenas guarda e valida parâmetros; não calcula pontos.
- Limites da interface serão lidos da configuração, não copiados como valores independentes no componente de cor.

### Seed fictício e bootstrap

- O seed gerará exatamente um administrador, uma recepcionista, um médico, dez sintomas com gravidades cobrindo 1 a 8 e seis pacientes.
- Identificadores e dados pessoais serão fabricados para desenvolvimento, sem importar ou consultar cadastros reais. Os CPFs de exemplo terão dígitos verificadores válidos, mas não serão usados como credenciais nem como dados de pessoas reais.
- A carga será idempotente e o reset limpará o estado antes de reconstruir o conjunto inicial. A inicialização da aplicação chamará o bootstrap de modo que execuções repetidas não dupliquem registros.
- Alternativa considerada: seed executado uma única vez por import de módulo. Rejeitada por não ser previsível com reload e por dificultar os testes de reset.

### Interface inicial

- A aplicação terá layout compartilhado com cabeçalho, navegação-base associada aos quatro perfis e mensagens padronizadas. A navegação é demonstrativa; não implica autenticação ou controle de acesso.
- `app/app.py` registrará a rota inicial com conteúdo em português e `html_lang="pt-BR"`. Componentes Reflex ficarão em `app/componentes/`; funções/páginas em `app/paginas/`.
- O componente de faixa receberá pontuação e configuração: vermelho para pontuação >= limite alto; laranja para >= limite médio; verde abaixo. A faixa não será um motor de priorização.
- O layout será validado em viewport próxima de 360 px e em notebook; não deve causar sobreposição ou rolagem horizontal involuntária.
- Alternativa considerada: implementar agora menus operacionais por perfil. Rejeitada por depender de autenticação e fluxos que estão explicitamente fora do escopo.

### Idioma e documentação

- Nomes públicos de domínio seguirão os nomes pedidos (`Usuario`, `Paciente`, `Sintoma`, `Atendimento`, `RegistroAuditoria`); identificadores e comentários novos serão em português, e textos apresentados ao usuário também.
- Documentos de governança ficarão em `openspec/project.md` e `openspec/checklist-geral.md`; premissas abertas ficarão em `docs/suposicoes.md`. O README cobrirá instalação, execução do Reflex e testes.
- A dependência de Reflex permanecerá na camada de apresentação; testes de domínio poderão importar os módulos sem inicializar a aplicação.

## Risks / Trade-offs

- [Dados em memória desaparecem ao reiniciar e não são compartilhados entre processos] → documentar o limite e não escalar horizontalmente esta versão.
- [Um CPF sintético com dígitos válidos pode coincidir com um identificador atribuído fora do projeto] → usar apenas valores artificiais no conjunto local, não solicitar dados de usuário real e confirmar a política de fixtures antes de distribuir ambientes compartilhados.
- [Menu por perfil pode ser confundido com autorização] → identificar claramente o menu como estrutura visual e manter autenticação/bloqueio de rotas fora do escopo.
- [Estado global mutável de configuração pode ser compartilhado por sessões no processo] → validar atualizações atomicamente e cobrir leituras/alterações concorrentes nos testes se a implementação permitir atualização em runtime.

## Migration Plan

1. Criar os pacotes, modelos, parâmetros, repositório e seed, preservando `rxconfig.py`, `requirements.txt` e `.gitignore`.
2. Construir os componentes e a página inicial, depois substituir a apresentação padrão em `app/app.py` e configurar `pt-BR`.
3. Executar `pytest` e iniciar `reflex run`; conferir a interface em celular e notebook.
4. Não há migração de dados: o estado atual é somente o scaffold inicial. Para rollback, restaurar a página anterior e remover os novos pacotes/documentos em uma alteração controlada; nenhuma persistência precisa ser convertida.

## Open Questions

- Confirmar, antes de usar os fixtures fora do ambiente local, a política de distribuição de CPFs sintéticos matematicamente válidos, pois validade de dígitos não comprova que um número nunca foi atribuído a uma pessoa.