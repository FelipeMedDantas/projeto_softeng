# Tasks

## 1. Estrutura e domínio

- [x] 1.1 Criar os pacotes e diretórios previstos (`app/dominio`, `app/dados`, `app/servicos`, `app/paginas`, `app/componentes`, `tests` e `docs`), preservando `rxconfig.py`, `requirements.txt` e `.gitignore`; verificar a presença dos diretórios e arquivos existentes.
- [x] 1.2 Implementar dataclasses e enums em `app/dominio/modelos.py` para as cinco entidades, quatro perfis e cinco status; acrescentar testes em `tests/test_base_projeto.py` e verificar com `pytest tests/test_base_projeto.py -k dominio`.
- [x] 1.3 Garantir que `app/dominio/` não importe Reflex e que os módulos do domínio importem sem inicializar a interface; verificar por teste isolado e inspeção dos imports do pacote.

## 2. Parâmetros configuráveis

- [x] 2.1 Implementar padrões, leitura, alteração validada e restauração em `app/dominio/parametros.py`; testar padrões, modos permitidos, rejeição de intervalo/capacidade inválidos, limites inconsistentes e preservação do estado anterior com `pytest tests/test_base_projeto.py -k parametros`.
- [x] 2.2 Validar que as mensagens de erro de configuração são claras e estão em português e que nenhuma atualização inválida altera parcialmente os parâmetros; cobrir as mensagens e o estado resultante em `tests/test_base_projeto.py`.

## 3. Repositório e seed

- [x] 3.1 Implementar repositório único em memória com `threading.Lock` ou `RLock`, operações CRUD genéricas e restauração do estado inicial; testar criação, leitura, atualização, remoção e reset com `pytest tests/test_base_projeto.py -k repositorio`.
- [x] 3.2 Implementar seed idempotente com 1 admin, 1 recepcionista, 1 médico, 10 sintomas de gravidades 1 a 8 e 6 pacientes com CPFs sintéticos de dígitos verificadores válidos; testar quantidades, gravidades, validação dos CPFs, ausência de duplicação e reset com `pytest tests/test_base_projeto.py -k seed`.
- [x] 3.3 Testar gravações concorrentes por múltiplas threads e confirmar que todos os registros concluídos continuam disponíveis sem corrupção, usando `pytest tests/test_base_projeto.py -k concorrente`.

## 4. Interface base

- [x] 4.1 Criar layout, mensagens e faixa de cor em `app/componentes/layout.py`, `app/componentes/mensagens.py` e `app/componentes/faixa_cor.py`, com menu visual por perfil e limites lidos da configuração; verificar classificação em cada fronteira de cor.
- [x] 4.2 Criar página inicial mínima em `app/paginas/` e registrar em `app/app.py` com `html_lang="pt-BR"`, seed idempotente no bootstrap e textos em português; iniciar com `reflex run` e confirmar que a rota inicial renderiza.
- [x] 4.3 Validar o layout em viewport de aproximadamente 360 px e em notebook, verificando uso dos controles sem sobreposição ou rolagem horizontal involuntária; confirmar que o menu não autentica nem bloqueia rotas.

## 5. Governança e documentação

- [x] 5.1 Criar `openspec/project.md`, `openspec/checklist-geral.md` e `docs/suposicoes.md` com stack, perfis, regras parametrizadas, convenções, fora de escopo, critérios obrigatórios de arquivamento e premissas marcadas `CONFIRMAR`; revisar consistência com as specs desta change.
- [x] 5.2 Criar README inicial com instalação, execução do app e testes; seguir os comandos nele documentados e confirmar que `pytest` é executável no ambiente do projeto.
- [x] 5.3 Verificar que comentários e mensagens novas ao usuário estão em português e que os exemplos/documentos não incorporam dados reais ou credenciais.

## 6. Integração

- [x] 6.1 Executar a suíte completa com `pytest` e corrigir falhas introduzidas pela fundação; confirmar que os testes de concorrência, seed, parâmetros e isolamento do domínio passam juntos.
- [x] 6.2 Iniciar a aplicação com `reflex run`, verificar a rota inicial em português brasileiro e conferir os layouts celular/notebook conforme a spec `base-projeto`.