"""
api.py
------
Thin Flask layer on top of the existing service classes.

Endpoints:
    GET    /                       -> serves the SPA (index.html)
    POST   /api/register           -> AuthService.register
    POST   /api/login              -> AuthService.login
    GET    /api/subjects           -> SubjectService.get_subjects_for_user
    POST   /api/subjects           -> SubjectService.add_subject
    DELETE /api/subjects/<int:id>  -> SubjectService.delete_subject
    POST   /api/generate-plan      -> PlannerService.generate_and_save
    GET    /api/plan               -> PlannerService.get_saved_plan
    GET    /api/health             -> simple health check

Authentication note
-------------------
This is a study/MVP API. After login/register the client receives the
`user_id` and passes it back on every subsequent call (header `X-User-Id`
or query string). For production use, replace this with proper session
cookies or JWT.

Run:
    cd "ExpoTech 2026/files"
    python api.py
"""

from __future__ import annotations

import os
import sys
from functools import wraps

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

sys.path.insert(0, os.path.dirname(__file__))

from auth_service import (
    AuthService,
    DuplicateEmailError,
    InvalidCredentialsError,
    ValidationError as AuthValidationError,
)
from connection import get_db
from planner_service import PlannerService
from subject_service import SubjectService, SubjectValidationError

app = Flask(__name__, template_folder="templates")
CORS(app)

_db = get_db()
_auth_svc = AuthService()
_subject_svc = SubjectService()
_planner_svc = PlannerService()


# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------
def _bootstrap() -> None:
    if not _db.test_connection():
        print("[FATAL] Não foi possível conectar ao MySQL. Verifique o .env.")
        sys.exit(1)
    _db.create_all_tables()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _json_error(message: str, status: int = 400):
    return jsonify({"ok": False, "error": message}), status


def _get_user_id_from_request() -> int | None:
    raw = request.headers.get("X-User-Id") or request.args.get("user_id")
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def require_user(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        user_id = _get_user_id_from_request()
        if user_id is None:
            return _json_error("Autenticação requerida (X-User-Id ausente).", 401)
        return view(user_id, *args, **kwargs)
    return wrapper


# ---------------------------------------------------------------------------
# Static / SPA
# ---------------------------------------------------------------------------
@app.get("/")
def home():
    return render_template("index.html")


@app.get("/api/health")
def health():
    return jsonify({"ok": True, "db": _db.test_connection()})


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
@app.post("/api/register")
def register():
    data = request.get_json(silent=True) or {}
    try:
        with _db.get_session() as session:
            user = _auth_svc.register(
                session,
                full_name=data.get("full_name", ""),
                email=data.get("email", ""),
                password=data.get("password", ""),
                confirm_password=data.get("confirm_password", data.get("password", "")),
                education_level=data.get("education_level", ""),
                course=data.get("course", ""),
            )
            return jsonify({"ok": True, "user": user.to_dict()})
    except AuthValidationError as exc:
        return _json_error(str(exc), 400)
    except DuplicateEmailError as exc:
        return _json_error(str(exc), 409)


@app.post("/api/login")
def login():
    data = request.get_json(silent=True) or {}
    try:
        with _db.get_session() as session:
            user = _auth_svc.login(
                session,
                email=data.get("email", ""),
                password=data.get("password", ""),
            )
            return jsonify({"ok": True, "user": user.to_dict()})
    except AuthValidationError as exc:
        return _json_error(str(exc), 400)
    except InvalidCredentialsError as exc:
        return _json_error(str(exc), 401)


# ---------------------------------------------------------------------------
# Subjects
# ---------------------------------------------------------------------------
@app.get("/api/subjects")
@require_user
def list_subjects(user_id: int):
    with _db.get_session() as session:
        items = _subject_svc.get_subjects_for_user(session, user_id)
        return jsonify({"ok": True, "subjects": [s.to_dict() for s in items]})


@app.post("/api/subjects")
@require_user
def create_subject(user_id: int):
    data = request.get_json(silent=True) or {}
    try:
        with _db.get_session() as session:
            subject = _subject_svc.add_subject(
                session,
                user_id=user_id,
                name=data.get("name", ""),
                difficulty=int(data.get("difficulty", 0)),
                priority=int(data.get("priority", 0)),
                exam_date_str=data.get("exam_date", ""),
            )
            return jsonify({"ok": True, "subject": subject.to_dict()})
    except (SubjectValidationError, ValueError) as exc:
        return _json_error(str(exc), 400)


@app.delete("/api/subjects/<int:subject_id>")
@require_user
def delete_subject(user_id: int, subject_id: int):
    with _db.get_session() as session:
        deleted = _subject_svc.delete_subject(session, subject_id, user_id)
        if not deleted:
            return _json_error("Matéria não encontrada.", 404)
        return jsonify({"ok": True})


# ---------------------------------------------------------------------------
# Planner
# ---------------------------------------------------------------------------
@app.post("/api/generate-plan")
@require_user
def generate_plan(user_id: int):
    data = request.get_json(silent=True) or {}
    try:
        hours_per_day = float(data.get("hours_per_day", 0))
        days_per_week = int(data.get("days_per_week", 0))
    except (TypeError, ValueError):
        return _json_error("Parâmetros inválidos.", 400)

    try:
        with _db.get_session() as session:
            subjects = _subject_svc.get_subjects_for_user(session, user_id)
            plan = _planner_svc.generate_and_save(
                session,
                user_id=user_id,
                subjects=subjects,
                hours_per_day=hours_per_day,
                days_per_week=days_per_week,
            )
            return jsonify({"ok": True, "plan": plan})
    except ValueError as exc:
        return _json_error(str(exc), 400)


@app.get("/api/plan")
@require_user
def get_plan(user_id: int):
    with _db.get_session() as session:
        plan = _planner_svc.get_saved_plan(session, user_id)
        return jsonify({"ok": True, "plan": plan})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    _bootstrap()
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
