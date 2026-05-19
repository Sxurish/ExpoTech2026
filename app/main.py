"""
main.py
-------
CLI do Study Planner. Autentica via Supabase Auth (mesmo usuário do front).

Run:
    python main.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv

from utils import (
    banner, section, success, error, info,
    prompt, prompt_int, prompt_float, prompt_password,
    format_minutes,
)
from connection import get_db
from planner_service import PlannerService
from subject_service import SubjectService, SubjectValidationError

load_dotenv()


def _supabase():
    """Lazy import: a lib só é usada na CLI; web não precisa do CLI."""
    from supabase import create_client
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    if not url or not key:
        error("SUPABASE_URL / SUPABASE_ANON_KEY não definidos no .env.")
        sys.exit(1)
    return create_client(url, key)


class StudyPlannerApp:
    def __init__(self) -> None:
        self._db = get_db()
        self._sb = _supabase()
        self._subject_svc = SubjectService()
        self._planner_svc = PlannerService()
        self._user_id: str | None = None
        self._user_label: str = ""

    def run(self) -> None:
        if not self._db.test_connection():
            error("Não foi possível conectar ao banco. Verifique DATABASE_URL no .env.")
            sys.exit(1)
        self._main_loop()

    def _main_loop(self) -> None:
        while True:
            if self._user_id is None:
                self._show_auth_menu()
            else:
                self._show_app_menu()

    # ======================================================================
    # Auth (Supabase)
    # ======================================================================
    def _show_auth_menu(self) -> None:
        banner("Planejador de Estudos  ·  Bem-vindo")
        print()
        print("  1. Cadastrar")
        print("  2. Entrar")
        print("  0. Sair")
        print()
        choice = prompt("Escolha uma opção")
        if choice == "1":
            self._register()
        elif choice == "2":
            self._login()
        elif choice == "0":
            info("Adeus! 👋")
            sys.exit(0)
        else:
            error("Opção inválida.")

    def _register(self) -> None:
        section("Criar Conta")
        full_name = prompt("Nome completo")
        email = prompt("E-mail")
        password = prompt_password("Senha (mín 6 caracteres)")
        education_level = prompt("Nível de escolaridade (ex: Graduação)")
        course = prompt("Curso / Graduação")
        try:
            self._sb.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "full_name": full_name,
                        "education_level": education_level,
                        "course": course,
                    }
                }
            })
            success("Conta criada! Confirme o e-mail (se exigido) e faça login.")
        except Exception as exc:  # noqa: BLE001
            error(f"Erro ao cadastrar: {exc}")

    def _login(self) -> None:
        section("Entrar")
        email = prompt("E-mail")
        password = prompt_password()
        try:
            resp = self._sb.auth.sign_in_with_password({"email": email, "password": password})
            user = resp.user
            if not user:
                error("Falha no login.")
                return
            self._user_id = str(user.id)
            meta = user.user_metadata or {}
            self._user_label = meta.get("full_name") or email
            success(f"Bem-vindo de volta, {self._user_label}!")
        except Exception as exc:  # noqa: BLE001
            error(f"E-mail ou senha inválidos. ({exc})")

    # ======================================================================
    # App menu
    # ======================================================================
    def _show_app_menu(self) -> None:
        banner(f"Planejador de Estudos  ·  {self._user_label}")
        print()
        print("  1. Adicionar matéria")
        print("  2. Ver minhas matérias")
        print("  3. Gerar plano de estudos")
        print("  4. Ver plano de estudos")
        print("  5. Excluir uma matéria")
        print("  6. Sair (logout)")
        print("  0. Sair")
        print()
        choice = prompt("Escolha uma opção")
        dispatch = {
            "1": self._add_subject,
            "2": self._view_subjects,
            "3": self._generate_plan,
            "4": self._view_plan,
            "5": self._delete_subject,
            "6": self._logout,
            "0": self._exit,
        }
        action = dispatch.get(choice)
        if action:
            action()
        else:
            error("Opção inválida.")

    def _add_subject(self) -> None:
        section("Adicionar Matéria")
        name = prompt("Nome da matéria")
        difficulty = prompt_int("Dificuldade", 1, 5)
        priority = prompt_int("Prioridade", 1, 5)
        exam_date = prompt("Data da prova (AAAA-MM-DD)")
        with self._db.get_session() as session:
            try:
                subj = self._subject_svc.add_subject(
                    session,
                    user_id=self._user_id,  # type: ignore[arg-type]
                    name=name,
                    difficulty=difficulty,
                    priority=priority,
                    exam_date_str=exam_date,
                )
                success(f"Matéria '{subj.name}' salva!")
            except SubjectValidationError as exc:
                error(str(exc))

    def _view_subjects(self) -> None:
        section("Minhas Matérias")
        with self._db.get_session() as session:
            subjects = self._subject_svc.get_subjects_for_user(session, self._user_id)  # type: ignore[arg-type]
        if not subjects:
            info("Nenhuma matéria ainda.")
            return
        print(f"\n  {'#':<4} {'Nome':<25} {'Dif':>4} {'Pri':>4} {'Data da Prova':>14}")
        print("  " + "-" * 56)
        for i, s in enumerate(subjects, 1):
            print(f"  {i:<4} {s.name:<25} {s.difficulty:>4} {s.priority:>4} {str(s.exam_date):>14}")

    def _delete_subject(self) -> None:
        section("Excluir Matéria")
        with self._db.get_session() as session:
            subjects = self._subject_svc.get_subjects_for_user(session, self._user_id)  # type: ignore[arg-type]
        if not subjects:
            info("Nada para excluir.")
            return
        self._view_subjects()
        idx = prompt_int("Número da matéria", 1, len(subjects))
        target = subjects[idx - 1]
        with self._db.get_session() as session:
            ok = self._subject_svc.delete_subject(session, target.id, self._user_id)  # type: ignore[arg-type]
        if ok:
            success(f"Matéria '{target.name}' excluída.")
        else:
            error("Matéria não encontrada.")

    def _generate_plan(self) -> None:
        section("Gerar Plano de Estudos")
        hours = prompt_float("Horas por dia", 0.5, 16)
        days = prompt_int("Dias por semana", 1, 7)
        with self._db.get_session() as session:
            subjects = self._subject_svc.get_subjects_for_user(session, self._user_id)  # type: ignore[arg-type]
            if not subjects:
                error("Adicione matérias antes de gerar um plano.")
                return
            try:
                plan = self._planner_svc.generate_and_save(
                    session,
                    user_id=self._user_id,  # type: ignore[arg-type]
                    subjects=subjects,
                    hours_per_day=hours,
                    days_per_week=days,
                )
                success("Plano gerado e salvo!")
                self._print_plan(plan)
            except ValueError as exc:
                error(str(exc))

    def _view_plan(self) -> None:
        section("Meu Plano de Estudos")
        with self._db.get_session() as session:
            plan = self._planner_svc.get_saved_plan(session, self._user_id)  # type: ignore[arg-type]
        if not plan:
            info("Nenhum plano encontrado. Gere um primeiro.")
            return
        self._print_plan(plan)

    @staticmethod
    def _print_plan(plan: dict) -> None:
        print()
        for day, rows in plan.items():
            print(f"  📅  \033[1m{day}\033[0m")
            total = 0
            for row in rows:
                minutes = row.get("study_time_minutes", 0)
                total += minutes
                name = row.get("subject_name", "—")
                print(f"       • {name:<30} {format_minutes(minutes):>10}")
            print(f"       {'Total':>35} {format_minutes(total):>10}")
            print()

    def _logout(self) -> None:
        info(f"Adeus, {self._user_label}!")
        try:
            self._sb.auth.sign_out()
        except Exception:  # noqa: BLE001
            pass
        self._user_id = None
        self._user_label = ""

    @staticmethod
    def _exit() -> None:
        info("Adeus! 👋")
        sys.exit(0)


if __name__ == "__main__":
    try:
        StudyPlannerApp().run()
    except KeyboardInterrupt:
        print("\n")
        info("Interrompido. Adeus!")
        sys.exit(0)
