# Repository Code Review (April 12, 2026)

## Scope reviewed

- `ExpoTech 2026/files/*.py`
- `ExpoTech 2026/files/schema.sql`
- `ExpoTech 2026/files/requirements.txt`
- `ExpoTech 2026/files/README.md`
- `ExpoTech 2026/package.json`

## Executive summary

The core Python business logic is generally readable and modular, but the current repository layout is inconsistent with the import paths used by the application. In its current state, the CLI cannot start (`ModuleNotFoundError: No module named 'auth'`).

The highest-priority fix is to align package structure and imports so the app can run. After that, focus on algorithm correctness refinements and test coverage.

## Findings

### 1) App is not runnable due to import/package mismatch (Critical)

- `main.py` imports modules via package paths like `auth.auth_service`, `cli.utils`, `database.connection`, `models`, and `services.*`.
- But all Python files currently live flat under `ExpoTech 2026/files/` (no `auth/`, `cli/`, `database/`, `models/`, `services/` directories with `__init__.py`).
- Result: startup fails with `ModuleNotFoundError`.

**Recommendation**
- Choose one of:
  1. Restructure files into the package layout described in README, or
  2. Change imports to match the current flat-file layout.
- Add a minimal smoke test that runs imports from `main.py`.

### 2) README and actual repository structure are out of sync (High)

- README describes a structured package layout (`study_planner/auth/...`, etc.).
- Actual repo has a single `files/` directory containing all Python modules.

**Recommendation**
- Update README to match reality, or reorganize code to match README.
- Keep one source of truth to reduce onboarding friction.

### 3) Planner “no consecutive repeats” behavior is not truly enforced (Medium)

- `_allocate_day` claims to avoid consecutive same-subject blocks.
- Current implementation creates one row per subject per day, so there are no repeated blocks to separate anyway.
- Insert-at-front/append logic is also non-obvious and may produce unintuitive ordering.

**Recommendation**
- If true block sequencing is required, represent plans as multiple blocks per day and perform a proper ordering pass.
- Otherwise, simplify comments and logic to reflect current behavior.

### 4) Minimal automated validation in repo (Medium)

- No tests are present despite README mentioning optional pytest usage.
- Basic compile check passes, but runtime import check fails.

**Recommendation**
- Add at least:
  - unit tests for `AuthService`, `SubjectService`, and `PlannerService`
  - integration smoke test for `main.py` imports
  - CI command for lint + tests

### 5) JavaScript dependency setup appears unrelated/noisy (Low)

- `package.json` includes `claude` and `pip`, while project is a Python CLI.
- Committed `node_modules/` increases repo noise and may confuse project intent.

**Recommendation**
- If Node is unnecessary, remove `package.json` and `node_modules/` from version control.
- If needed for tooling, document why and add a focused scripts section.

## Positive observations

- Clear service separation (`auth_service`, `subject_service`, `planner_service`).
- Good use of SQLAlchemy ORM and session context manager.
- Password hashing via bcrypt.
- Input validation exists in key service methods.

## Suggested remediation order

1. Fix Python package/import structure so the app runs.
2. Add smoke tests for startup and core service behavior.
3. Reconcile README and on-disk layout.
4. Refine planner sequencing logic or simplify to match actual behavior.
5. Clean up repo artifacts (`node_modules`) unless intentionally required.

