# Design

## Context

Ver proposal.md para motivação e spec delta para o contrato observável. Hoje `app/app.py` registra somente `/` e `/login`; a guarda ASGI valida sessão, mas não perfil. O layout apresenta rótulos demonstrativos, e o login sempre redireciona para `/`. Sessões, usuários e auditoria usam o repositório compartilhado em memória.

## Goals / Non-Goals

**Goals:**
- Aplicar a mesma matriz de autorização às rotas, à navegação e às operações de serviço.
- Preservar destinos pós-login sem permitir redirecionamentos externos ou rotas não autorizadas.
- Tornar negações e rotas inexistentes distinguíveis, auditáveis quando aplicável e sem vazamento de conteúdo protegido.

**Non-Goals:**
- Criar login, credenciais, emissão de sessão ou fluxo de identificação de paciente.
- Implementar os fluxos operacionais de recepção, atendimento médico ou administração.
- Adicionar persistência externa ou mudar o formato dos tokens de sessão.

## Decisions

### Uma política central de rotas e permissões

Manter uma única matriz no domínio de autorização, associando cada rota ao conjunto de perfis permitido e cada operação de serviço aos perfis autorizados. A guarda ASGI e o layout consultam essa política; serviços verificam a permissão novamente no próprio limite. O menu é uma conveniência de navegação, nunca a fronteira de segurança.

Alternativa considerada: replicar verificações em cada página e callback. Foi rejeitada por permitir divergência entre páginas, menu e operações chamadas diretamente.

### Ordem da guarda e destino pós-login

Reconhecer primeiro recursos públicos, páginas 403/404 e caminhos inexistentes; então validar a sessão e, por fim, o perfil exigido pela rota. Sessão ausente em rota protegida redireciona a `/login` com o caminho local solicitado como candidato `next`; sessão válida sem permissão recebe 403. A API de login valida `next` no servidor após conhecer o perfil e devolve apenas uma rota local autorizada, ou a rota inicial do perfil. O cliente nunca decide se um destino é permitido.

Usar parsing estruturado de URL para rejeitar esquema, autoridade, caminhos protocol-relative ou malformados; comparar o caminho resultante à matriz antes de aceitar. Alternativa considerada: aceitar qualquer caminho iniciado por `/`; foi rejeitada porque isso não impede URLs protocol-relative nem garante autorização por perfil.

### Páginas de erro separadas do middleware

Registrar `/403` e `/404` como páginas acessíveis sem autenticação. A guarda não deve transformar caminhos inexistentes em redirecionamentos de login: a resolução de rota precisa preceder a autorização, e somente caminhos registrados como protegidos exigem sessão. A página 403 não inclui dados da rota negada.

Alternativa considerada: gerar uma resposta de erro diretamente no middleware ASGI. Foi rejeitada para manter mensagens, layout e idioma no padrão visual do projeto.

### Autorização no serviço e trilha de auditoria

Operações de serviço recebem uma identidade já resolvida no servidor, verificam o perfil permitido antes de qualquer mutação e lançam `PermissionError` em caso de negação. Registrar a negação no repositório compartilhado com o identificador interno do ator e a operação, estendendo a API de auditoria sem guardar token, senha ou hash.

Alternativa considerada: depender somente da guarda de páginas. Foi rejeitada porque callbacks ou chamadas internas podem invocar serviços sem passar pela navegação.

### Destinos e perfis propostos

Adotar, para revisão, `recepcao` em `/recepcao` e `/perfil`, `medico` em `/medico` e `/perfil`, `paciente` em `/paciente`, e `admin` apenas em `/admin` e `/perfil`. O limite de `admin` segue menor privilégio. `/paciente` terá rota e política, mas nenhuma credencial ou sessão de paciente será criada; o acesso efetivo depende de um fluxo de sessão de paciente futuro. Essas decisões de produto aguardam aprovação antes da implementação.

Alternativa considerada: conceder ao administrador acesso amplo a todas as áreas. Foi rejeitada por ausência de requisito e por ampliar privilégios sem necessidade demonstrada.

## Risks / Trade-offs

- [Rota registrada fora da matriz] → Testar o inventário de rotas contra a política e garantir que rotas protegidas desconhecidas falhem fechadas.
- [Política de serviço diverge da interface] → Testar permissões por serviço diretamente, sem montar a interface, além dos testes de navegação.
- [Integração futura de paciente não existe] → Manter o fluxo de credenciais fora desta change e cobrir a política de `/paciente` com identidade sintética.
- [Mudança de `next` afeta compatibilidade do login] → Manter a raiz como fallback para sessões já autenticadas e validar destinos no servidor antes de alterar o callback.
- [Novo evento de auditoria amplia categorias aceitas] → Restringir a ação a uma categoria explícita de negação e testar que detalhes não contenham credenciais ou tokens.

## Migration Plan

Não há migração de dados: sessões e usuários permanecem no repositório em memória. Registrar as novas páginas e políticas de forma aditiva, atualizar a guarda e o callback de login, e então trocar os links demonstrativos pelos destinos autorizados. Para rollback, remover os registros e políticas novos e retornar o callback ao redirecionamento atual para `/`; nenhuma estrutura persistida precisa ser revertida.