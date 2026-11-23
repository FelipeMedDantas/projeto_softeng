# Proposal

## Why

O projeto Reflex ainda contém apenas a página inicial padrão, sem uma fundação coerente para o Sistema de Priorização de Atendimento. Esta change estabelece contratos de domínio, configuração, dados fictícios em memória e interface-base antes da implementação de fluxos clínicos, preservando privacidade e separação arquitetural desde o início.

## What Changes

- Definir modelos de domínio, perfis, estados de atendimento e parâmetros de negócio configuráveis com validação em português.
- Estabelecer armazenamento compartilhado exclusivamente em memória, centralizado em um repositório protegido por lock, além de seed fictício e reinicializável.
- Substituir a página inicial padrão por uma interface mínima em português, com `html_lang="pt-BR"`, layout responsivo e componentes-base reutilizáveis.
- Documentar governança, premissas, instalação, execução, testes e os critérios gerais para arquivar changes.
- Criar testes automatizados para os contratos da fundação, incluindo concorrência, validação, seed/reset e isolamento do domínio em relação ao Reflex.
- Manter fora desta change autenticação, autorização de rotas, cálculo da pontuação, ordenação da fila e telas específicas de cada perfil.

## Capabilities

### New Capabilities
- `base-projeto`: fundação do domínio, parâmetros configuráveis, armazenamento fictício em memória e interface-base Reflex.

### Modified Capabilities

Nenhuma. O diretório `openspec/specs/` ainda não contém capacidades definidas.

## Impact

- Código previsto: `app/dominio/`, `app/dados/`, `app/servicos/`, `app/paginas/`, `app/componentes/` e `app/app.py`.
- Testes: `tests/test_base_projeto.py`, usando `pytest` e testes concorrentes para o repositório em memória.
- Configuração e documentação: `requirements.txt`, `.gitignore`, `README.md`, `openspec/project.md`, `openspec/checklist-geral.md` e `docs/suposicoes.md`.
- Stack: Python 3.11+, Reflex para interface e pytest; sem banco externo, Xano ou persistência compartilhada fora do processo.
- Branch de trabalho prevista: `change/01-base-projeto`.