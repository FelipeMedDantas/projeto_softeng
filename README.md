# Sistema de Priorização de Atendimento

Aplicação fictícia para desenvolvimento e demonstração de uma base de pronto atendimento. Não substitui avaliação clínica ou protocolos profissionais. Todos os dados de exemplo são fictícios.

## Requisitos

- Python 3.11 ou superior
- `uv` para criar o ambiente e instalar as dependências

## Instalação

Na raiz do projeto, execute:

```bash
uv venv --python 3.11 .venv
source .venv/bin/activate
uv pip install --python .venv/bin/python -r requirements.txt
```

## Executar

Com o ambiente virtual ativado:

```bash
reflex run
```

A aplicação estará disponível no endereço local informado pelo Reflex.

## Contas de demonstração

Use estas contas fictícias apenas em ambientes locais de demonstração:

| Perfil | E-mail | Senha |
| --- | --- | --- |
| Administração | `admin@example.test` | `DemoAdmin-02!` |
| Recepção | `recepcao@example.test` | `DemoRecepcao-02!` |
| Médico | `medico@example.test` | `DemoMedico-02!` |

Não reutilize essas credenciais em outros sistemas ou ambientes. O seed guarda apenas hashes com salt; as senhas são usadas somente para criar os hashes do conjunto fictício.

## Rotas e acesso

| Perfil | Rota inicial | Rotas permitidas |
| --- | --- | --- |
| Recepção | `/recepcao` | `/recepcao`, `/perfil` |
| Médico | `/medico` | `/medico`, `/perfil` |
| Paciente | `/paciente` | `/paciente` |
| Administração | `/admin` | `/admin`, `/perfil` |

A rota `/` encaminha visitantes para `/login` e usuários autenticados para a rota inicial do perfil. Após o login, `next` só é aceito quando identifica uma rota local permitida ao perfil; nos demais casos, usa-se a rota inicial. Uma sessão válida sem permissão recebe a página 403; caminhos não registrados recebem a página 404.

`/paciente` e sua política de acesso estão preparadas, mas esta versão não oferece credenciais, identificação nem criação de sessão para pacientes. O menu exibe somente links permitidos ao perfil confirmado pelo servidor; a autorização também é verificada nas rotas e operações protegidas.

## Testes

Com o ambiente virtual ativado:

```bash
python -m pytest
```

O armazenamento é apenas em memória e é reiniciado quando o processo da aplicação termina. Não use dados pessoais reais.