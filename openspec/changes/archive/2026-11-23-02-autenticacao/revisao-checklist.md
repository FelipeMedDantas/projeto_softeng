# Revisão da Checklist de Arquivamento

Change: `02-autenticacao`  
Data: 2026-11-23  
Resultado: revisão concluída para o escopo da change.

| Área da checklist | Resultado registrado | Evidência ou justificativa |
| --- | --- | --- |
| Funcionalidade e erros | Atendido | Login válido/inválido, mensagem genérica, conta desativada, bloqueio, sessão, expiração e logout cobertos por pytest; 53 testes passaram na suíte completa. |
| Parâmetros configuráveis | Atendido | Duração, tentativas, bloqueio e iterações de hash têm padrões e validação positiva; atualizações inválidas preservam o estado. |
| Dados fictícios e segredos | Atendido com limite de demonstração | As três contas usam domínio `.test`; seed guarda somente hash com salt. README alerta que senhas são exclusivas para demonstração local. Testes não encontraram senhas/tokens em auditoria ou resposta JSON. |
| Permissão e sessão | Atendido no escopo | Sessões, falhas e auditoria ficam no repositório com lock; o guard ASGI bloqueia a raiz/páginas internas sem sessão antes de entregar conteúdo. Login e endpoints de autenticação permanecem públicos. |
| Autorização completa | Fora do escopo | Regras de autorização por recurso, páginas 403/404 e mapa completo de rotas pertencem à Change 03. |
| Dados compartilhados e concorrência | Atendido | Repositório central em memória protegido por `RLock`; testes cobrem contagem concorrente e transições de sessão/tentativa. |
| Interface responsiva e idioma | Atendido | `/login` usa `html_lang="pt-BR"`; medidas e inspeção visual em 360 px e 1366 px não encontraram overflow. Cores computadas dos campos são branco/escuro/cinza solicitadas, com foco visível e botões contrastantes. |
| Qualidade | Atendido com aviso não bloqueante | `pytest`: 53 passaram; `reflex compile --dry`: sucesso; OpenSpec e spec principal validaram estritamente. Há somente aviso de depreciação do `TestClient` no Starlette instalado. |
| Documentação e OpenSpec | Atendido | README documenta as credenciais de teste e o uso local; 16/16 tarefas completas; spec principal `autenticacao` sincronizada e validada. |
| Execução local | Atendido em porta isolada | App testado em `localhost:3010` com Python 3.11.15. Instâncias antigas Python 3.10 em 3001/8000 não foram encerradas; não fazem parte deste build. |
