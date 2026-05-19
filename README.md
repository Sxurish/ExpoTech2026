# Study Planner — Python + Supabase (CLI + Web + Vercel)

Planejador de estudos modular que gera, de forma automática, um cronograma
semanal personalizado com base na dificuldade, prioridade e urgência da
prova de cada matéria.

Dois pontos de entrada compartilham o **mesmo núcleo de regras de negócio**:

- **CLI** — `python main.py`
- **Web (Flask local)** — `python app/api.py` e abra `http://localhost:5000`
- **Web (Vercel)** — deploy serverless via `vercel.json` + `api/index.py`

Banco: **Supabase Postgres**. Autenticação: **Supabase Auth** (`@supabase/supabase-js` no front).

---

## Estrutura do projeto

```
.
├── main.py                  # launcher CLI (delega para app/main.py)
├── requirements.txt         # deps que a Vercel instala
├── vercel.json              # config de deploy serverless
├── api/
│   └── index.py             # entry serverless da Vercel (expõe o Flask app)
└── app/
    ├── api.py               # Flask: rotas /api/* + SPA
    ├── main.py              # CLI
    ├── connection.py        # SQLAlchemy engine (Postgres)
    ├── supabase_client.py   # valida JWT (Authorization: Bearer)
    ├── subject_service.py
    ├── planner_service.py
    ├── subject.py           # model Subject
    ├── study_plan.py        # model StudyPlan
    ├── utils.py             # helpers de CLI
    ├── schema.sql           # SQL para colar no SQL Editor do Supabase
    ├── templates/index.html # SPA single-page
    ├── requirements.txt     # deps usadas localmente (espelha a da raiz)
    └── .env.example
```

---

## Pré-requisitos

- Python 3.10+
- Conta Supabase com um projeto criado
- (Para deploy) conta Vercel

---

## 1) Preparar o Supabase

1. Vá no SQL Editor do projeto e cole o conteúdo de `app/schema.sql`. Clique em **Run**.
   - Cria as tabelas `subjects` e `study_plans` (uuid → `auth.users`)
   - Habilita RLS com policies `auth.uid() = user_id`
2. Em **Project Settings → API**, copie:
   - `Project URL` → `SUPABASE_URL`
   - `anon` `public` key → `SUPABASE_ANON_KEY`
3. Em **Project Settings → Database → Connection pooler** (modo **Transaction**, porta **6543**), copie a Connection String → `DATABASE_URL`. Substitua `[YOUR-PASSWORD]` pela senha do banco.

> **Por que o pooler?** Cold starts serverless abrem/fecham conexões a todo
> instante; usar o pooler do Supabase (PgBouncer) evita esgotar conexões.

---

## 2) Rodar localmente

```bash
cd app
python -m venv .venv
source .venv/bin/activate                # Linux/macOS
# .venv\Scripts\activate                # Windows
pip install -r requirements.txt
cp .env.example .env                     # preencha DATABASE_URL, SUPABASE_URL, SUPABASE_ANON_KEY
python api.py                            # abre http://localhost:5000
```

CLI:

```bash
cd ..
python main.py
```

---

## 3) Deploy na Vercel

1. Importe o repositório na Vercel (**New Project**).
2. Em **Environment Variables**, configure:
   - `DATABASE_URL`
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
3. Deploy. A Vercel detecta `vercel.json` + `requirements.txt` automaticamente e
   constrói `api/index.py` como função Python.

A rota `/(.*)` é redirecionada para o handler Flask em `api/index.py`, que serve
tanto a SPA (`/`) quanto os endpoints (`/api/*`).

---

## Endpoints da API

| Método | Rota                  | Auth | Descrição |
|---|---|---|---|
| GET    | `/`                   | —    | Serve a SPA |
| GET    | `/api/health`         | —    | Ping do banco |
| GET    | `/api/subjects`       | Bearer | Lista matérias |
| POST   | `/api/subjects`       | Bearer | Cria matéria |
| DELETE | `/api/subjects/<id>`  | Bearer | Remove matéria |
| POST   | `/api/generate-plan`  | Bearer | Gera plano semanal |
| GET    | `/api/plan`           | Bearer | Lê último plano salvo |

> Auth = header `Authorization: Bearer <access_token>` do Supabase. O front faz
> login direto via `@supabase/supabase-js` e injeta o token nas chamadas.

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

### 3. Distribuição

```
TempoPorMatéria = (Score / SomaDosScores) × MinutosDoDia
```

### 4. Restrições

- Mínimo **30 min**, máximo **120 min** por matéria por dia
- Arredondado para o múltiplo de **30 min** mais próximo
- Total ajustado para bater exatamente com as horas disponíveis

---

## Checklist de segurança

- [x] Autenticação delegada ao **Supabase Auth** (sem armazenar senhas)
- [x] **RLS** ativo em `subjects` e `study_plans` (defesa em profundidade — mesmo se a API tivesse bug, o banco isola por `auth.uid()`)
- [x] JWT validado no backend a cada request (`Authorization: Bearer`)
- [x] Credenciais via env vars (`DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`); nenhuma no código
- [x] SQL Injection bloqueado pelo ORM SQLAlchemy
