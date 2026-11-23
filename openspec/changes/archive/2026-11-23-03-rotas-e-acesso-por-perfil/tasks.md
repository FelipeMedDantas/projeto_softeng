# Tasks

## 1. Política e limite dos serviços

- [x] 1.1 Criar a política central de rotas por perfil e cobrir a matriz completa, inclusive `/perfil`, com testes unitários de permissões e negações.
- [x] 1.2 Criar a verificação de perfil para operações de serviço e a auditoria de acesso negado no repositório; testar chamada direta sem permissão, ausência de mutação e registro sem credenciais ou tokens.

## 2. Guarda HTTP e destino pós-login

- [x] 2.1 Atualizar a guarda ASGI para distinguir rotas públicas, protegidas e inexistentes, validar sessão e perfil e encaminhar negações a 403; testar sessão ausente, expirada, permitida e negada.
- [x] 2.2 Preservar `next` no fluxo de login e validá-lo no servidor contra a política de rotas; testar destino local permitido, externo, malformado e não autorizado, com fallback para a rota inicial do perfil.

## 3. Páginas e navegação

- [x] 3.1 Registrar as páginas iniciais protegidas de recepção, médico, paciente e administração, além de 403 e 404; testar o inventário e os destinos registrados sem adicionar emissão de sessão de paciente.
- [x] 3.2 Atualizar o layout para mostrar apenas links permitidos ao perfil confirmado pelo servidor; testar os links de cada perfil e verificar uso em viewport de aproximadamente 360 px e notebook.
- [x] 3.3 Atualizar o README com a matriz de rotas e os limites de autenticação desta change; conferir que a documentação corresponde à política implementada.

## 4. Verificação integrada

- [x] 4.1 Cobrir o fluxo integrado de acesso anônimo, redirecionamento pós-login, autorização por perfil, 403, 404 e auditoria; executar `python -m pytest` e corrigir somente falhas relacionadas a esta change.
- [x] 4.2 Iniciar a aplicação conforme o comando documentado e verificar navegação e páginas de erro em viewport de celular e notebook, sem redirecionamento externo ou conteúdo protegido exposto.