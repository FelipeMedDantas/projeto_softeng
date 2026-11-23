# Proposal

## Why

A autenticação atual identifica o perfil da equipe, mas as rotas ainda não aplicam uma política uniforme de acesso por perfil. Definir essa política agora protege as páginas e operações existentes e estabelece um contrato para as próximas áreas do sistema.

## What Changes

- Definir o destino inicial e as rotas permitidas para cada perfil, incluindo o tratamento de `/`, `/next`, acesso negado e rota inexistente.
- Aplicar autorização por perfil na navegação e nas operações de serviço, registrando tentativas negadas sem expor credenciais ou tokens.
- Criar páginas protegidas iniciais por perfil e páginas de erro 403 e 404, com navegação coerente e responsiva.
- Preparar `/paciente` e sua guarda de acesso, sem introduzir autenticação, credenciais ou criação de sessão de paciente nesta change.
- Restringir provisoriamente `admin` a `/admin` e `/perfil`, adotando menor privilégio.

## Capabilities

### New Capabilities
- `rotas-e-acesso-por-perfil`: destinos, autorização de rotas e operações por perfil, navegação e tratamento de acesso negado.

### Modified Capabilities
- Nenhuma. As capabilities de autenticação e fundação permanecem inalteradas; esta change especifica o mapeamento e a autorização das novas rotas.

## Impact

- Código previsto: registro de rotas, guarda ASGI de autenticação/autorização, navegação do layout, callbacks de login e novo serviço de autorização.
- Interface prevista: páginas iniciais protegidas para recepção, médico, paciente e administração; páginas 403 e 404.
- Testes previstos: matriz perfil-rota, redirecionamentos e validação de `next`, guarda de sessão, autorização em serviços, auditoria de negações e responsividade.
- Não adiciona dependências nem altera o armazenamento de autenticação.