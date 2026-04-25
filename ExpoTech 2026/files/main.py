"""
main.py
-------
Entry point for the Study Planner CLI application.

Run with:
    python main.py
"""

from __future__ import annotations

import sys

# Ensure the project root is on sys.path when running directly
import os
sys.path.insert(0, os.path.dirname(__file__))

from auth_service import (
    AuthService,
    DuplicateEmailError,
    InvalidCredentialsError,
    ValidationError as AuthValidationError,
)
from utils import (
    banner, section, success, error, info,
    prompt, prompt_int, prompt_float, prompt_password,
    format_minutes, clear,
)
from connection import get_db
from user import User
from subject import Subject
from study_plan import StudyPlan
from planner_service import PlannerService
from subject_service import SubjectService, SubjectValidationError


# ---------------------------------------------------------------------------
# Application class
# ---------------------------------------------------------------------------
class StudyPlannerApp:
    def __init__(self) -> None:
        self._db = get_db()
        self._auth_svc = AuthService()
        self._subject_svc = SubjectService()
        self._planner_svc = PlannerService()
        self._current_user: User | None = None

    # ======================================================================
    # Bootstrap
    # ======================================================================
    def run(self) -> None:
        self._bootstrap_db()
        self._main_loop()

    def _bootstrap_db(self) -> None:
        if not self._db.test_connection():
            error("Não foi possível conectar ao MySQL. Verifique seu arquivo .env e tente novamente.")
            sys.exit(1)
        self._db.create_all_tables()

    # ======================================================================
    # Main loop
    # ======================================================================
    def _main_loop(self) -> None:
        while True:
            if self._current_user is None:
                self._show_auth_menu()
            else:
                self._show_app_menu()

    # ======================================================================
    # Auth menu
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
        full_name      = prompt("Nome completo")
        email          = prompt("E-mail")
        password       = prompt_password("Senha (mín 6 caracteres)")
        confirm        = prompt_password("Confirmar senha")
        education_lvl  = prompt("Nível de escolaridade (ex: Graduação)")
        course         = prompt("Curso / Graduação")

        with self._db.get_session() as session:
            try:
                user = self._auth_svc.register(
                    session,
                    full_name=full_name,
                    email=email,
                    password=password,
                    confirm_password=confirm,
                    education_level=education_lvl,
                    course=course,
                )
                success(f"Conta criada! Bem-vindo, {user.full_name}. Por favor, entre.")
            except (AuthValidationError, DuplicateEmailError) as exc:
                error(str(exc))

    def _login(self) -> None:
        section("Entrar")
        email    = prompt("E-mail")
        password = prompt_password()

        with self._db.get_session() as session:
            try:
                user = self._auth_svc.login(session, email=email, password=password)
                # Detach so we can use the object outside the session
                session.expunge(user)
                self._current_user = user
                success(f"Bem-vindo de volta, {user.full_name}!")
            except (AuthValidationError, InvalidCredentialsError) as exc:
                error(str(exc))

    # ======================================================================
    # App menu (logged in)
    # ======================================================================
    def _show_app_menu(self) -> None:
        assert self._current_user is not None
        banner(f"Planejador de Estudos  ·  {self._current_user.full_name}")
        print()
        print("  1. Adicionar matéria")
        print("  2. Ver minhas matérias")
        print("  3. Gerar plano de estudos")
        print("  4. Ver plano de estudos")
        print("  5. Excluir uma matéria")
        print("  6. Sair")
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
            error("Invalid option.")

    # ======================================================================
    # Subjects
    # ======================================================================
    def _add_subject(self) -> None:
        section("Adicionar Matéria")
        name       = prompt("Nome da matéria")
        difficulty = prompt_int("Dificuldade", 1, 5)
        priority   = prompt_int("Prioridade", 1, 5)
        exam_date  = prompt("Data da prova (AAAA-MM-DD)")

        with self._db.get_session() as session:
            try:
                subj = self._subject_svc.add_subject(
                    session,
                    user_id=self._current_user.id,  # type: ignore[union-attr]
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
            subjects = self._subject_svc.get_subjects_for_user(
                session, self._current_user.id  # type: ignore[union-attr]
            )

        if not subjects:
            info("Nenhuma matéria ainda. Adicione algumas primeiro.")
            return

        print(
            f"\n  {'#':<4} {'Nome':<25} {'Dif':>4} {'Pri':>4} {'Data da Prova':>12}"
        )
        print("  " + "-" * 54)
        for i, s in enumerate(subjects, 1):
            print(
                f"  {i:<4} {s.name:<25} {s.difficulty:>4} {s.priority:>4} "
                f"{str(s.exam_date):>12}"
            )

    def _delete_subject(self) -> None:
        section("Excluir Matéria")
        with self._db.get_session() as session:
            subjects = self._subject_svc.get_subjects_for_user(
                session, self._current_user.id  # type: ignore[union-attr]
            )

        if not subjects:
            info("Nenhuma matéria para excluir.")
            return

        self._view_subjects()
        idx = prompt_int("Digite o número da matéria para excluir", 1, len(subjects))
        target = subjects[idx - 1]

        with self._db.get_session() as session:
            ok = self._subject_svc.delete_subject(
                session, target.id, self._current_user.id  # type: ignore[union-attr]
            )
        if ok:
            success(f"Matéria '{target.name}' excluída.")
        else:
            error("Matéria não encontrada.")

    # ======================================================================
    # Study plan
    # ======================================================================
    def _generate_plan(self) -> None:
        section("Gerar Plano de Estudos")
        hours_per_day = prompt_float("Horas disponíveis por dia", 0.5, 16)
        days_per_week = prompt_int("Dias disponíveis por semana", 1, 7)

        with self._db.get_session() as session:
            subjects = self._subject_svc.get_subjects_for_user(
                session, self._current_user.id  # type: ignore[union-attr]
            )
            if not subjects:
                error("Adicione matérias antes de gerar um plano.")
                return

            try:
                plan = self._planner_svc.generate_and_save(
                    session,
                    user_id=self._current_user.id,  # type: ignore[union-attr]
                    subjects=subjects,
                    hours_per_day=hours_per_day,
                    days_per_week=days_per_week,
                )
                success("Plano de estudos gerado e salvo!")
                self._print_plan(plan)
            except ValueError as exc:
                error(str(exc))

    def _view_plan(self) -> None:
        section("Meu Plano de Estudos")
        with self._db.get_session() as session:
            plan = self._planner_svc.get_saved_plan(
                session, self._current_user.id  # type: ignore[union-attr]
            )

        if not plan:
            info("Nenhum plano de estudos encontrado. Gere um primeiro.")
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

    # ======================================================================
    # Session management
    # ======================================================================
    def _logout(self) -> None:
        info(f"Adeus, {self._current_user.full_name}!")  # type: ignore[union-attr]
        self._current_user = None

    @staticmethod
    def _exit() -> None:
        info("Adeus! 👋")
        sys.exit(0)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app = StudyPlannerApp()
    try:
        app.run()
    except KeyboardInterrupt:
        print("\n")
        info("Interrompido. Adeus!")
        sys.exit(0)
