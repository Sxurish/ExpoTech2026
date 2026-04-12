# 📚 Study Planner — Python + MySQL CLI Application

A production-ready, modular Study Planner that automatically generates
personalised weekly study schedules based on subject difficulty, priority,
and exam urgency.

---

## Project Structure

```
study_planner/
├── auth/
│   ├── __init__.py
│   └── auth_service.py        # Registration & login (bcrypt)
├── cli/
│   ├── __init__.py
│   └── utils.py               # CLI helpers, coloured output
├── database/
│   ├── __init__.py
│   ├── connection.py          # SQLAlchemy engine + session factory
│   └── schema.sql             # Raw SQL schema (reference only)
├── models/
│   ├── __init__.py
│   ├── user.py                # User ORM model
│   ├── subject.py             # Subject ORM model
│   └── study_plan.py          # StudyPlan ORM model
├── services/
│   ├── __init__.py
│   ├── subject_service.py     # CRUD + validation for subjects
│   └── planner_service.py     # Plan generation algorithm + persistence
├── main.py                    # CLI entry point
├── requirements.txt
├── .env.example
└── README.md
```

---

## Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.10 + |
| MySQL  | 8.0 + |

---

## Setup

### 1. Clone / Download the project

```bash
cd study_planner
```

### 2. Create a virtual environment

```bash
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create the MySQL database

Log into MySQL and run:

```sql
CREATE DATABASE IF NOT EXISTS study_planner
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;
```

The application creates all tables automatically on first run.
If you prefer to run the schema manually:

```bash
mysql -u root -p study_planner < database/schema.sql
```

### 5. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` with your MySQL credentials:

```env
DB_HOST=localhost
DB_PORT=3306
DB_NAME=study_planner
DB_USER=root
DB_PASSWORD=your_password
```

### 6. Run the application

```bash
python main.py
```

---

## Features

| Feature | Detail |
|---|---|
| Register / Login | bcrypt-hashed passwords, email validation |
| Add Subjects | Name, Difficulty (1–5), Priority (1–5), Exam Date |
| Generate Plan | Urgency + score algorithm, proportional time distribution |
| View Plan | Coloured weekly schedule with totals |
| Delete Subject | Remove a subject and regenerate the plan |
| Data Persistence | All data stored in MySQL between sessions |
| SQL Injection safe | SQLAlchemy ORM with parameterised queries |

---

## Algorithm

### 1. Urgency Weight

| Days until exam | Weight |
|---|---|
| 0 – 3 | 5 (Very Urgent) |
| 4 – 7 | 4 |
| 8 – 14 | 3 |
| 15 + | 1 |

### 2. Composite Score

```
Score = (Urgency × 0.5) + (Difficulty × 0.3) + (Priority × 0.2)
```

### 3. Time Distribution

```
TimePerSubject = (Score / TotalScore) × DailyMinutes
```

### 4. Constraints

- Minimum **30 min** per subject per day
- Maximum **120 min** per subject per day
- Time rounded to nearest **30 min**
- Total daily time adjusted to exactly match available hours
- No two consecutive blocks of the same subject

---

## Architecture Notes

- **Clean separation of concerns** — business logic lives entirely in `services/`,
  CLI interaction in `main.py` / `cli/`, data access via SQLAlchemy ORM.
- **Flask-ready** — `AuthService`, `SubjectService`, and `PlannerService`
  accept a SQLAlchemy `Session` via dependency injection; they can be called
  identically from a Flask route.
- **No raw SQL** — all queries go through the ORM, preventing SQL injection.
- **Environment-based config** — no credentials in source code.

---

## Running Tests (optional)

```bash
pip install pytest
pytest tests/
```

---

## Security Checklist

- [x] Passwords hashed with `bcrypt`
- [x] SQL Injection prevented via SQLAlchemy ORM
- [x] Credentials loaded from `.env` (never hardcoded)
- [x] Email uniqueness enforced at DB level
- [x] Input validation before any DB write
