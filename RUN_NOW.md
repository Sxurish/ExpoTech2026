# Como rodar o projeto agora

## 1) Entrar na pasta correta

```bash
cd "/workspace/ExpoTech2026/ExpoTech 2026/files"
```

No Windows (PowerShell):

```powershell
cd "C:\caminho\para\ExpoTech2026\ExpoTech 2026\files"
```

> Se você estiver na raiz do repositório, agora também pode rodar `python main.py`
> (launcher adicionado na raiz).

## 2) Criar e ativar ambiente virtual

```bash
python -m venv .venv
source .venv/bin/activate
```

## 3) Instalar dependências

```bash
pip install -r requirements.txt
```

## 4) Subir o MySQL (obrigatório)

A aplicação usa MySQL via `mysql+mysqlconnector`.
Você precisa ter um servidor MySQL rodando e acessível.

Exemplo (local):
- Host: `localhost`
- Porta: `3306`
- Banco: `study_planner`

Crie o banco:

```sql
CREATE DATABASE IF NOT EXISTS study_planner
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
```

Opcional: carregar schema manualmente

```bash
mysql -u root -p study_planner < schema.sql
```

## 5) Configurar variáveis de ambiente

Crie um arquivo `.env` dentro de `ExpoTech 2026/files/` com:

```env
DB_HOST=localhost
DB_PORT=3306
DB_NAME=study_planner
DB_USER=root
DB_PASSWORD=sua_senha
```

## 6) Rodar a aplicação

```bash
python main.py
```

Alternativas úteis:

```bash
# a partir da raiz do repositório
python main.py

# ou apontando direto para o arquivo da aplicação
python "ExpoTech 2026/files/main.py"
```

Se aparecer:

- `Cannot connect to MySQL...`

significa que o MySQL não está rodando, ou host/porta/usuário/senha no `.env` estão incorretos.

## 7) Checagem rápida de diagnóstico

```bash
python -m py_compile *.py
python main.py
```

O primeiro comando valida sintaxe dos módulos.
O segundo testa inicialização e conexão com banco.
