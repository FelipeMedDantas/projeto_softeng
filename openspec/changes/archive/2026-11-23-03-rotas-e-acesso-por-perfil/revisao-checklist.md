# Revisão da Checklist de Arquivamento

Change: `03-rotas-e-acesso-por-perfil`  
Data: 2026-11-23  
Resultado: revisão concluída para o escopo da change; sincronização da nova capability aguarda decisão de arquivamento.

| Área da checklist | Resultado registrado | Evidência ou justificativa |
| --- | --- | --- |
| Funcionalidade e erros | Atendido | `pytest`: 107 testes passaram. Há cobertura de destinos pós-login, sessão ausente/expirada, matriz de perfil × rota, 403/404 e chamadas de serviço negadas. No navegador, recepção ao acessar diretamente `/admin` foi redirecionada a `/403`, sem conteúdo administrativo. |
| Regras de negócio, limites e reset | Não aplicável | Esta change não altera parâmetros de negócio, armazenamento ou regras de reset. |
| Dados fictícios e segredos | Atendido | Testes usam perfis e contas fictícias do domínio `example.test`; não foram adicionados dados reais nem segredos. Auditoria de negação contém somente ator e identificador técnico da operação. |
| Permissão e segurança | Atendido | O `on_load` valida sessão no servidor, consulta a matriz central de rotas e mantém o conteúdo oculto até confirmar a rota atual. ASGI e serviços também verificam permissão; o menu não é usado como fronteira de segurança. |
| Estado compartilhado e concorrência | Atendido | Usuários, sessões e auditoria permanecem no repositório em memória existente, protegido por `RLock`; testes exercitam negação sem mutação e auditoria. |
| Interface responsiva e idioma | Atendido | Páginas e erros foram verificados em 360 px e 1280 px sem overflow horizontal; textos permanecem em português e `html_lang` é `pt-BR`. |
| Qualidade | Atendido com aviso não bloqueante | `pytest`: 107 passaram; `reflex compile --dry`: sucesso; não há diagnósticos nos arquivos alterados. Resta um aviso de depreciação do `Starlette TestClient`. |
| Documentação e OpenSpec | Parcial, aguardando decisão de sincronização | README, proposal, delta spec, design e tasks estão coerentes; tasks: 9/9. A nova capability `rotas-e-acesso-por-perfil` ainda não existe em `openspec/specs/`; sincronizar criará a spec principal a partir dos requisitos ADDED. |
| Execução local | Atendido | Reflex compilou e a navegação foi verificada. Os processos de teste foram encerrados; as portas 3000 e 8000 ficaram livres. |