# Checklist Geral para Arquivamento

Antes de arquivar qualquer change, revisar e registrar os resultados aplicáveis a todos os itens abaixo. Um item fora do escopo deve ter justificativa explícita na change; não deve ser marcado como aprovado por omissão.

## Funcionalidade

- [ ] Requisitos e cenários da change foram implementados e verificados com testes ou evidência observável.
- [ ] Casos de erro, limites e restauração/estado inicial relevantes foram testados.
- [ ] Regras de negócio leem parâmetros configuráveis; não há cópias divergentes de valores de negócio.
- [ ] Dados de demonstração e testes são inteiramente fictícios.

## Permissão e Segurança

- [ ] Cada rota, ação e conjunto de dados sensíveis tem o controle de acesso exigido pelo escopo; menu ou perfil visual não é tratado como autorização.
- [ ] Identidade e perfil são validados no servidor quando houver autenticação; não se confia apenas no estado do navegador.
- [ ] Não foram adicionados segredos, dados reais, credenciais ou integrações externas não aprovadas.
- [ ] Dados compartilhados estão na camada de repositório definida, com proteção contra concorrência apropriada; estado Reflex por sessão não é usado como armazenamento global.
- [ ] Tratamento de erros não expõe dados pessoais nem detalhes internos desnecessários.

## Interface Responsiva

- [ ] Fluxos incluídos na change foram verificados em viewport de aproximadamente 360 px e em notebook.
- [ ] Não há texto, controles ou navegação sobrepostos, inacessíveis ou cortados; não há rolagem horizontal involuntária.
- [ ] Mensagens, rótulos e idioma estão em português e o documento usa `html_lang="pt-BR"`.
- [ ] Estados de carregamento, vazio, sucesso e erro relevantes estão apresentados de forma compreensível.

## Qualidade

- [ ] Testes pytest focados e suíte aplicável passam; falhas pré-existentes ou não relacionadas estão identificadas.
- [ ] O domínio continua importável sem Reflex e as fronteiras de arquitetura foram respeitadas.
- [ ] Concorrência, validação e limites foram exercitados quando relevantes.
- [ ] Mudanças mantêm compatibilidade e não alteram arquivos alheios à change sem justificativa.
- [ ] A aplicação inicia pelo comando documentado e não depende de armazenamento ou serviço externo não autorizado.

## Documentação e OpenSpec

- [ ] README, instruções de instalação, execução, testes e documentação técnica correspondem ao comportamento atual.
- [ ] Suposições não confirmadas estão registradas e não são apresentadas como requisitos aprovados.
- [ ] Specs refletem os requisitos entregues; proposal, design e tasks têm estado coerente com a implementação.
- [ ] O resultado da revisão desta checklist foi registrado antes do arquivamento.