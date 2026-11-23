# Tasks

## 1. Modelo e parâmetros

- [x] 1.1 Estender `Usuario` com e-mail normalizado e `senha_hash`, preservando `ativo` e compatibilidade dos usos existentes; cobrir modelo e unicidade do e-mail em `tests/test_autenticacao.py` e executar `pytest tests/test_autenticacao.py -k usuario`.
- [x] 1.2 Adicionar `tempo_sessao_min=30`, `max_tentativas_login=5`, `tempo_bloqueio_min=5` e `iteracoes_hash_senha=600000` aos parâmetros, validando inteiros maiores que zero e restauração dos padrões; testar defaults e rejeições em `tests/test_autenticacao.py -k parametros`.

## 2. Hash e seed de demonstração

- [x] 2.1 Implementar criação e verificação de hash com PBKDF2-HMAC-SHA256, salt aleatório individual, custo configurado e comparação segura; testar senha correta/incorreta, salt distinto e ausência de senha em texto puro com `pytest tests/test_autenticacao.py -k hash`.
- [x] 2.2 Atualizar seed para as três contas fictícias de equipe, guardando somente `senha_hash`, e documentar no README as credenciais de demonstração e o aviso de uso exclusivamente local; testar carga idempotente, perfis, e-mails e hashes com `pytest tests/test_autenticacao.py -k seed`.
- [x] 2.3 Garantir bootstrap idempotente do seed ao obter o repositório global e no startup da aplicação; testar que as três contas conseguem autenticar sem chamar o seed manualmente com `pytest tests/test_autenticacao.py -k seed_global`.

## 3. Repositório de autenticação
- [x] 3.1 Adicionar operações atômicas protegidas por `RLock` para tentativas, bloqueio, sessões e invalidação, sem expor coleções privadas; testar contadores e acessos simultâneos em `tests/test_autenticacao.py -k repositorio`.
- [x] 3.2 Centralizar auditoria de sucesso, falha, bloqueio e logout no repositório, sem guardar senha, hash de senha, token bruto/digest ou e-mail desconhecido nos detalhes; testar conteúdo auditado e privacidade com `pytest tests/test_autenticacao.py -k auditoria`.

## 4. Serviço de autenticação

- [x] 4.1 Implementar login de equipe, normalização de e-mail, erro genérico, recusa de conta desativada e bloqueio no máximo configurado, aceitando `agora`; cobrir login válido/inválido, usuário desativado, cinco falhas, tempo restante, liberação e reset de contador com `pytest tests/test_autenticacao.py -k login`.
- [x] 4.2 Implementar criação/renovação/expiração de sessão por inatividade e logout invalidável, aceitando `agora`; cobrir expiração no limite de 30 minutos, atividade e retorno após logout com `pytest tests/test_autenticacao.py -k sessao`.

## 5. Endpoints e interface

- [x] 5.1 Criar endpoints server-side de login, validação de sessão e logout com cookie HttpOnly/SameSite e Secure em produção, redigindo corpos sensíveis dos logs; testar cabeçalhos, respostas e ausência de token em payload com `pytest tests/test_autenticacao.py -k endpoint`.
- [x] 5.2 Criar `/login` responsiva com campos de e-mail/senha, alternância mostrar/ocultar e submissão por Enter, mantendo `html_lang="pt-BR"`; validar compilação com `reflex compile --dry` e renderização da rota.
- [x] 5.3 Integrar o botão `Sair` ao layout, invalidar sessão e redirecionar a `/login`; verificar também retorno ao histórico sem revalidar a sessão e destino `/` para os três perfis até existirem páginas próprias.
- [x] 5.4 Proteger `/` e páginas internas com o layout protegido, ocultando conteúdo até validar sessão e redirecionando sessão ausente/expirada para `/login`; testar a verificação de sessão e redirecionamento.
- [x] 5.5 Definir contraste explícito nos inputs, placeholders, foco e botões da tela de login; validar estilo compilado e legibilidade em 360 px/notebook.

## 6. Integração

- [x] 6.1 Executar `pytest` completo e corrigir regressões introduzidas pela autenticação; confirmar cobertura de parâmetros, hash, bloqueio, sessões, auditoria, UI/API e compatibilidade dos testes da Change 01.
- [x] 6.2 Iniciar com `reflex run`, validar e-mail/senha, guard de `/`, idioma, mensagens e ausência de rolagem horizontal em viewport de aproximadamente 360 px e notebook; confirmar que logout remove a sessão e que não há acesso de equipe concedido por estado visual.