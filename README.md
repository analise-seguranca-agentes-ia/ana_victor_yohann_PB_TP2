# TP2 - Projeto de Bloco: Análise e Segurança de Agentes de IA

## Objetivo
TP2 do Projeto de Bloco de Análise e Segurança de Agentes de IA, continuação do 
[TP1](https://github.com/analise-seguranca-agentes-ia/ana_victor_yohann_PB_TP1). 
Este TP aprofunda o projeto em duas frentes:

- **EDA completo** do Customer Support Ticket Dataset: análise univariada e 
  multivariada, correlações, identificação de outliers e anomalias, e formulação 
  de hipóteses validadas com testes estatísticos formais (t-test / Mann-Whitney);
- **API FastAPI segura**: persistência em SQLite com SQLModel, controle de acesso 
  por ownership (anti-BOLA), modelos Pydantic com `extra='forbid'`, headers HTTP 
  de segurança, CORS com allowlist explícita, rate limiting no login e auditoria 
  por scan passivo do OWASP ZAP.

O objetivo é deixar a base do sistema de atendimento ao cliente robusta, tanto 
no entendimento dos dados quanto na segurança da API, servindo de base para o 
modelo de ML e o agente dos próximos TPs. A API também será alvo de um pentest 
em um TP futuro, por isso os controles do OWASP Top 10 já são aplicados agora.

## Equipe
- Ana Beatriz Rangel Mattos
- Victor Henrique Watanabe
- Yohann Matheus Gusso Guedes

## Dataset
**Customer Support Ticket Dataset**, disponível no Kaggle:
https://www.kaggle.com/datasets/suraj520/customer-support-ticket-dataset/data

O arquivo já está versionado neste repositório em `data/customer_support_tickets.csv`.
A fonte, as principais características e o motivo da escolha do dataset estão 
documentados na seção 1 do notebook.

## Estrutura de pastas
```
TP2/
├── data/                        # dataset original
│   └── customer_support_tickets.csv
├── eda/
│   ├── eda.ipynb                # EDA completo, hipóteses e testes estatísticos
│   └── requirements.txt
├── fastapi/
│   ├── main.py                  # ponto de entrada + middlewares (headers, CORS, SlowAPI)
│   ├── database.py              # engine e sessão SQLModel
│   ├── sqlite_database.py       # criação e população inicial do banco (sqlite3)
│   ├── database.db              # banco SQLite com usuários e predictions de exemplo
│   ├── limiter.py               # instância do rate limiter (SlowAPI)
│   ├── requirements.txt
│   ├── models/                  # tabelas SQLModel e modelos Pydantic (extra='forbid')
│   ├── routes/                  # endpoints (auth, health, prediction, user)
│   └── security/                # JWT + OAuth2PasswordBearer e RBAC
├── tests/                       # testes automatizados com pytest
├── zap/
│   ├── zap_report.html          
│   └── scan_passivo_zap.md      
└── README.md
```

## Pré-requisitos
- Python 3.10 ou superior (o código utiliza unions do tipo `str | None`)
- `pip`
- [OWASP ZAP](https://www.zaproxy.org/download/) (apenas para reproduzir o scan)

Opcionalmente, crie um ambiente virtual antes de instalar as dependências:

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # Linux/macOS
```

## EDA - Instruções

### Dependências

Para instalar as dependências do notebook, execute:

```bash
cd eda
pip install -r requirements.txt
```

### Pacotes Utilizados

- pandas: Leitura e manipulação do dataset;
- numpy: Operações numéricas;
- matplotlib: Geração dos gráficos;
- seaborn: Visualizações estatísticas;
- scipy: Testes de hipótese (t-test / Mann-Whitney);
- jupyter: Execução do notebook.

### Etapas do EDA

O notebook está organizado nas seguintes etapas:

1. Compreensão do problema e do dataset
2. Inspeção inicial
3. Verificação da qualidade dos dados
4. Limpeza e preparação dos dados
5. Análise univariada
6. Análise multivariada
7. Identificação de outliers e anomalias
8. Documentação do EDA e conclusões


### Execução

Inicie o Jupyter com:

```bash
cd eda
jupyter notebook eda.ipynb
```

Ou, se preferir, abra o arquivo `eda/eda.ipynb` diretamente no VS Code (com as 
extensões *Python* e *Jupyter* instaladas) e execute as células por lá.

Em ambos os casos o notebook roda a partir do diretório `eda/`, o que é 
necessário porque ele lê o dataset pelo caminho relativo 
`../data/customer_support_tickets.csv`.

## FastAPI - Instruções

### Dependências

Para instalar as dependências necessárias, execute:

```bash
cd fastapi
pip install -r requirements.txt
```

### Pacotes Utilizados

- fastapi[standard]: Framework web;
- uvicorn: Servidor para execução da API;
- pydantic: Validação e tipagem de dados;
- sqlmodel: ORM para modelos e consultas ao banco SQLite;
- pyjwt: Geração e verificação de tokens;
- pwdlib[argon2]: Hashing de senhas;
- slowapi: Rate limiting;
- email-validator: Validação de e-mails nos modelos.

### Banco de dados (SQLite)

O banco `fastapi/database.db` possui duas tabelas:

| Tabela | Descrição |
|---|---|
| `user` | Usuários da API (id, username, roles, e-mail, nome e hash da senha) |
| `prediction` | Predições de intenção, cada uma com um `owner_id` (FK para `user.user_id`) que identifica seu proprietário |

A criação e a população inicial são feitas pelo script 
[fastapi/sqlite_database.py](fastapi/sqlite_database.py), utilizando `sqlite3`. 
O seed cria dois usuários (`johndoe` e `janedoe`) e uma prediction para cada um, 
o que permite demonstrar o controle de acesso por ownership.

O banco é criado e populado **automaticamente** ao iniciar a API, pois o 
`database.py` chama `init_and_seed_db()` na inicialização. O caminho do banco é 
resolvido a partir da pasta do código, então ele sempre é criado em 
`fastapi/database.db`, independentemente do diretório de onde a API ou os testes 
são executados. Para criá-lo manualmente, execute:

```bash
cd fastapi
python -c "from sqlite_database import init_and_seed_db; init_and_seed_db()"
```

O seed só insere dados se a tabela `user` estiver vazia, então executar o script 
mais de uma vez não duplica registros. Para recriar o banco do zero, apague o 
arquivo `fastapi/database.db` e execute o comando acima novamente.

O `sqlite3` é usado apenas na criação/população inicial. Todas as consultas 
realizadas pela API utilizam **SQLModel**, sem SQL raw.

### Execução

A partir do diretório `fastapi/` (os imports da aplicação dependem disso), 
inicie o servidor com um dos dois comandos:

```bash
python main.py
```

ou

```bash
uvicorn main:app --reload
```

No Linux/macOS, use `python3 main.py` caso `python` não esteja disponível.

- **API URL:** `http://127.0.0.1:8000`
- **Documentação Swagger:** `http://127.0.0.1:8000/docs`

### Rotas

| Método | Rota | Protegida | Descrição |
|---|---|---|---|
| `GET` | `/health` | Não | Verifica se a API está ativa |
| `POST` | `/auth/token` | Não | Autentica o usuário (form-urlencoded) e retorna o token JWT. Limitada a **10 requisições/minuto** por cliente |
| `POST` | `/auth/register` | Não | Cadastra um novo usuário com `{"username", "password"}` |
| `GET` | `/users` | Sim (admin) | Lista os usuários cadastrados |
| `POST` | `/predictions/predict` | Sim (Bearer) | Recebe `{"text": "..."}`, salva a prediction com o usuário autenticado como proprietário e retorna `201` |
| `GET` | `/predictions` | Sim (Bearer) | Lista apenas as predictions do usuário autenticado |
| `GET` | `/predictions/{id}` | Sim (Bearer) | Retorna a prediction pelo ID somente se ela pertencer ao usuário autenticado (`403` caso pertença a outro usuário, `404` caso não exista) |

#### Autenticação

Para testar as rotas protegidas, autentique-se via `/auth/token` ou use o botão `Authorize` no Swagger com um dos seguintes usuários:

##### Usuário admin:

Username: `johndoe`
Password: `johndoe123`

##### Usuário normal

Username: `janedoe`
Password: `janedoe123`

## Testes - Instruções

### Dependências

O `pytest` já está incluído no `fastapi/requirements.txt`. Caso ainda não tenha 
instalado as dependências da API, execute:

```bash
cd fastapi
pip install -r requirements.txt
```

### Execução

A partir da **raiz do projeto**, execute:

```bash
python -m pytest tests -v
```

O arquivo [tests/conftest.py](tests/conftest.py) adiciona o diretório `fastapi/` 
ao `sys.path` e direciona a aplicação para um **banco temporário**, criado e 
populado com o mesmo seed (`johndoe` e `janedoe`) a cada execução e removido ao 
final. Assim, os testes sempre partem do mesmo estado e não alteram o 
`fastapi/database.db` versionado.

Os tokens JWT são gerados uma única vez por execução, para não consumir o 
limite de 10 requisições/minuto do `/auth/token`.

### Cenários cobertos

Os testes estão em [tests/test_security.py](tests/test_security.py):

| Teste | Cenário | Resultado esperado |
|---|---|---|
| `test_access_without_token` | Acesso a `GET /predictions` sem token JWT | `401 Unauthorized` |
| `test_access_other_user_resource_bola` | `johndoe` cria uma prediction e `janedoe` tenta acessá-la pelo ID (BOLA) | `403 Forbidden` |
| `test_reject_extra_fields_in_request_body` | Envio do campo extra `role` no body de `POST /predictions/predict` | `422 Unprocessable Entity` com erro do tipo `extra_forbidden` no campo `role` |
| `test_rate_limit_on_auth_token` | 11 tentativas de login com senha errada em sequência (simulação de brute force) | `401` nas 10 primeiras e `429 Too Many Requests` na 11ª |

