# Governança do Projeto

## Propósito

O Sistema de Priorização de Atendimento é uma aplicação fictícia para apoiar a organização inicial de atendimentos em pronto atendimento hospitalar. Esta base serve a desenvolvimento e demonstração; não substitui avaliação clínica, protocolos institucionais ou sistemas de saúde reais.

## Stack e Arquitetura

- Python 3.11 ou superior, Reflex para a interface e pytest para testes.
- Dados exclusivamente em memória: não usar banco externo, Xano nem persistência remota.
- `rx.State` representa estado por sessão de navegador. Estado compartilhado entre sessões fica centralizado em `app/dados/repositorio.py`, protegido por `threading.Lock` ou `threading.RLock`.
- `app/dominio/`, `app/dados/` e `app/servicos/` contêm domínio, dados e serviços Python puros; não importam Reflex. `app/dominio/` não pode depender da interface.
- `app/paginas/` e `app/componentes/` contêm a apresentação Reflex. A interface chama serviços e não concentra regras de negócio.
- Estrutura de referência: `app/dominio/` (`modelos.py`, `parametros.py`), `app/dados/` (`repositorio.py`, `seed.py`), `app/servicos/`, `app/paginas/`, `app/componentes/` (`layout.py`, `faixa_cor.py`, `mensagens.py`), `tests/`, `docs/` e `openspec/`.

## Perfis

- `recepcao`: perfil de recepção.
- `medico`: perfil médico.
- `paciente`: perfil de paciente; o fluxo futuro de identificação está previsto com CPF e número do paciente.
- `admin`: perfil administrativo.

Perfis e menus visuais não equivalem a autenticação nem a autorização. Mudanças que introduzam acesso a dados ou ações protegidas devem especificar e implementar controle de acesso explicitamente.

## Regras Parametrizadas

Regras de negócio devem ler parâmetros configuráveis e não espalhar valores fixos em componentes ou serviços.

- Pontuação final limitada a `[1, 10]`: gravidade dos sintomas segundo `modo_gravidade` (`maior`, padrão; `soma`; `media`) + prioridade legal + bônus de espera.
- Prioridade legal: idade `>= idade_idoso` (padrão 60), gestante ou idade `<= idade_crianca` (padrão 12); soma `prioridade_legal_pontos` (padrão 1) uma única vez, sem acumular condições.
- Bônus de espera: `+1` a cada `intervalo_bonus_min` (padrão 30 minutos), limitado a `teto_bonus` (padrão 7).
- Faixa visual: vermelho quando pontuação `>= limite_alta` (padrão 8); laranja quando `>= limite_media` (padrão 5); verde abaixo do limite médio.
- Capacidade padrão da fila: `capacidade_fila` = 30.
- Configurações inválidas devem ser rejeitadas com mensagem clara em português, sem alteração parcial do estado.

O motor de pontuação, a definição de arredondamento e as regras de ordenação só são considerados parte do sistema quando uma change os especificar; os valores desta seção não autorizam presumir fluxos clínicos.

## Privacidade e Dados

- Todo dado de seed, demonstração, documentação e teste deve ser fictício. Nunca inserir dados identificáveis de pacientes, profissionais ou instituições reais.
- CPFs de seed devem ser artificiais e satisfazer a validação matemática dos dígitos verificadores, sem uso como credenciais reais. A validade matemática não prova que o número nunca foi atribuído; a distribuição desses fixtures em ambientes compartilhados requer confirmação explícita.
- Registrar apenas os dados necessários ao escopo aprovado. Não enviar dados a serviços externos.

## Convenções

- Código, comentários, documentação do projeto e mensagens visíveis ao usuário em português. Nomes de APIs e dependências podem conservar grafia técnica convencional.
- Definir o idioma do documento como `html_lang="pt-BR"`.
- Manter regras de negócio em Python puro; interface Reflex limitada à apresentação e coordenação de eventos.
- Mudanças planejadas pelo OpenSpec devem ter nomes kebab-case e branches no padrão `change/<nome-da-change>` (para esta fundação: `change/01-base-projeto`).
- Adicionar testes pytest focados nos contratos e manter README e documentação coerentes com os comandos executáveis.

## Fora de Escopo Base

- Persistência em banco ou serviços externos.
- Diagnóstico, recomendação médica, decisão clínica automatizada ou substituição de protocolos profissionais.
- Login/autenticação, bloqueio de rotas por perfil e telas específicas de recepção, médico, paciente ou administrador, salvo em changes futuras.
- Motor de cálculo de pontuação e ordenação da fila nesta Change 01.