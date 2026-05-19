"""
api.py
------
Camada Flask sobre os serviços de domínio.

Autenticação é **Supabase Auth** (registro/login acontecem no front via
@supabase/supabase-js). O front envia o access token JWT em
`Authorization: Bearer <jwt>` em todas as chamadas /api/*; o backend valida
com a Supabase e extrai o `user_id` (UUID).

Endpoints:
    GET    /                       -> serve a SPA (index.html)
    GET    /api/health             -> ping do banco
    GET    /api/subjects           -> SubjectService.get_subjects_for_user
    POST   /api/subjects           -> SubjectService.add_subject
    DELETE /api/subjects/<int:id>  -> SubjectService.delete_subject
    POST   /api/generate-plan      -> PlannerService.generate_and_save
    GET    /api/plan               -> PlannerService.get_saved_plan
"""

from __future__ import annotations

import os
import sys
from functools import wraps

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

sys.path.insert(0, os.path.dirname(__file__))

from connection import get_db
from planner_service import PlannerService
from subject_service import SubjectService, SubjectValidationError
from supabase_client import get_user_id_from_jwt

app = Flask(__name__, template_folder="templates")
CORS(app)

_subject_svc = SubjectService()
_planner_svc = PlannerService()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _json_error(message: str, status: int = 400):
    return jsonify({"ok": False, "error": message}), status


def _extract_bearer_token() -> str | None:
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        return header[len("Bearer "):].strip() or None
    return None


def require_user(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        token = _extract_bearer_token()
        if not token:
            return _json_error("Autenticação requerida (Authorization Bearer ausente).", 401)
        user_id = get_user_id_from_jwt(token)
        if not user_id:
            return _json_error("Token inválido ou expirado.", 401)
        return view(user_id, *args, **kwargs)
    return wrapper


# ---------------------------------------------------------------------------
# Static / SPA
# ---------------------------------------------------------------------------
@app.get("/")
def home():
    return render_template(
        "index.html",
        supabase_url=os.getenv("SUPABASE_URL", ""),
        supabase_anon_key=os.getenv("SUPABASE_ANON_KEY", ""),
    )


@app.get("/api/health")
def health():
    return jsonify({"ok": True, "db": get_db().test_connection()})


# ---------------------------------------------------------------------------
# Subjects
# ---------------------------------------------------------------------------
@app.get("/api/subjects")
@require_user
def list_subjects(user_id: str):
    with get_db().get_session() as session:
        items = _subject_svc.get_subjects_for_user(session, user_id)
        return jsonify({"ok": True, "subjects": [s.to_dict() for s in items]})


@app.post("/api/subjects")
@require_user
def create_subject(user_id: str):
    data = request.get_json(silent=True) or {}
    try:
        with get_db().get_session() as session:
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
def delete_subject(user_id: str, subject_id: int):
    with get_db().get_session() as session:
        deleted = _subject_svc.delete_subject(session, subject_id, user_id)
        if not deleted:
            return _json_error("Matéria não encontrada.", 404)
        return jsonify({"ok": True})


# ---------------------------------------------------------------------------
# Planner
# ---------------------------------------------------------------------------
@app.post("/api/generate-plan")
@require_user
def generate_plan(user_id: str):
    data = request.get_json(silent=True) or {}
    try:
        hours_per_day = float(data.get("hours_per_day", 0))
        days_per_week = int(data.get("days_per_week", 0))
    except (TypeError, ValueError):
        return _json_error("Parâmetros inválidos.", 400)

    try:
        with get_db().get_session() as session:
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
def get_plan(user_id: str):
    with get_db().get_session() as session:
        plan = _planner_svc.get_saved_plan(session, user_id)
        return jsonify({"ok": True, "plan": plan})


# ---------------------------------------------------------------------------
# Entry point (uso local — Vercel usa api/index.py)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
