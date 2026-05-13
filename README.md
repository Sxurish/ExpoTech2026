# Study Planner — Python + MySQL (CLI + Web)

Planejador de estudos modular que gera, de forma automática, um cronograma
semanal personalizado com base na dificuldade, prioridade e urgência da
prova de cada matéria.

Dois pontos de entrada compartilham o **mesmo núcleo de regras de negócio**:

- **CLI** — `python main.py`
- **Web (Flask)** — `python "ExpoTech 2026/files/api.py"` e abra `http://localhost:5000`

---

## Por que existem dois arquivos `main.py`

- `main.py` (raiz do repositório): launcher leve para você rodar `python main.py`
  direto da pasta raiz do projeto.
- `ExpoTech 2026/files/main.py`: entry point real da aplicação CLI, com toda a
  lógica.

São **intencionalmente diferentes** e **não duplicam regra de negócio**.

---

## Estrutura do projeto

```
ExpoTech 2026/files/
├── main.py                    # Entry point da CLI
├── api.py                     # API web em Flask (consome os mesmos services)
├── templates/
│   └── index.html             # Front-end single-page
├── auth_service.py            # Cadastro e login (bcrypt)
├── subject_service.py         # CRUD + validação de matérias
├── planner_service.py         # Algoritmo de geração do plano + persistência
├── connection.py              # Engine SQLAlchemy + session factory
├── user.py                    # Model ORM de usuário
├── subject.py                 # Model ORM de matéria
├── study_plan.py              # Model ORM do plano de estudos
├── utils.py                   # Helpers da CLI (output colorido, prompts)
├── schema.sql                 # Schema SQL bruto (referência)
├── .env.example               # Template do .env
└── requirements.txt
```

---

## Pré-requisitos

| Requisito | Versão |
|---|---|
| Python | 3.10 + |
| MySQL  | 8.0 + |

---

## Instalação

### 1. Entre na pasta do projeto

```bash
cd "ExpoTech 2026/files"
```

### 2. Crie um ambiente virtual

```bash
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Crie o banco MySQL

Entre no MySQL e rode:

```sql
CREATE DATABASE IF NOT EXISTS study_planner
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;
```

As tabelas são criadas automaticamente na primeira execução da aplicação.
Se preferir aplicar o schema manualmente:

```bash
mysql -u root -p study_planner < schema.sql
```

### 5. Configure as variáveis de ambiente

```bash
cp .env.example .env
```

Edite o `.env` com suas credenciais do MySQL:

```env
DB_HOST=localhost
DB_PORT=3306
DB_NAME=study_planner
DB_USER=root
DB_PASSWORD=sua_senha
```

### 6. Rode a aplicação

**Modo CLI:**

```bash
python main.py                 # a partir da raiz do repositório
# ou
python "ExpoTech 2026/files/main.py"
```

**Modo Web (Flask):**

```bash
cd "ExpoTech 2026/files"
python api.py
# abra http://localhost:5000
```

Endpoints da API web:

| Método | Rota | Descrição |
|---|---|---|
| GET    | `/`                      | Serve a SPA |
| POST   | `/api/register`          | Cria conta |
| POST   | `/api/login`             | Autentica |
| GET    | `/api/subjects`          | Lista as matérias do usuário (requer `X-User-Id`) |
| POST   | `/api/subjects`          | Cria matéria |
| DELETE | `/api/subjects/<id>`     | Remove matéria |
| POST   | `/api/generate-plan`     | Gera plano semanal |
| GET    | `/api/plan`              | Lê o último plano salvo |
| GET    | `/api/health`            | Ping do banco |

---

## Funcionalidades

| Recurso | Detalhe |
|---|---|
| Cadastro / Login | Senhas com hash bcrypt e validação de e-mail |
| Cadastrar matérias | Nome, Dificuldade (1–5), Prioridade (1–5), Data da prova |
| Gerar plano | Algoritmo de urgência + score com distribuição proporcional de tempo |
| Visualizar plano | Cronograma semanal colorido (CLI) ou em cards (Web) |
| Excluir matéria | Remove uma matéria e regenera o plano |
| Persistência | Dados gravados no MySQL entre sessões |
| Seguro contra SQL Injection | ORM SQLAlchemy com queries parametrizadas |

---

## Algoritmo

### 1. Peso de urgência

| Dias até a prova | Peso |
|---|---|
| 0 – 3 | 5 (Muito urgente) |
| 4 – 7 | 4 |
| 8 – 14 | 3 |
| 15 + | 1 |

### 2. Score composto

```
Score = (Urgência × 0,5) + (Dificuldade × 0,3) + (Prioridade × 0,2)
```

### 3. Distribuição do tempo

```
TempoPorMatéria = (Score / SomaDosScores) × MinutosDoDia
```

### 4. Restrições

- Mínimo de **30 min** por matéria por dia
- Máximo de **120 min** por matéria por dia
- Tempo arredondado para o múltiplo de **30 min** mais próximo
- Total diário ajustado para bater exatamente com as horas disponíveis
- Sem blocos consecutivos da mesma matéria

---

## Notas de arquitetura

- **Separação de responsabilidades** — a regra de negócio vive inteiramente em
  `services/`, a interação CLI em `main.py`, o acesso a dados via ORM SQLAlchemy.
- **Pronto para Flask** — `AuthService`, `SubjectService` e `PlannerService`
  recebem uma `Session` do SQLAlchemy via injeção de dependência, podendo ser
  chamados de uma rota Flask sem alteração.
- **Sem SQL bruto** — todas as queries passam pelo ORM, prevenindo SQL injection.
- **Configuração via ambiente** — nenhuma credencial no código-fonte.

---

## Rodando testes (opcional)

```bash
pip install pytest
pytest tests/
```

---

## Checklist de segurança

- [x] Senhas com hash via `bcrypt`
- [x] SQL Injection bloqueado pelo ORM SQLAlchemy
- [x] Credenciais carregadas do `.env` (nunca no código)
- [x] Unicidade de e-mail garantida no nível do banco
- [x] Validação de entrada antes de qualquer escrita no banco
