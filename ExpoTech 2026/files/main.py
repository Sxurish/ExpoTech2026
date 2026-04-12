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

from auth.auth_service import (
    AuthService,
    DuplicateEmailError,
    InvalidCredentialsError,
    ValidationError as AuthValidationError,
)
from cli.utils import (
    banner, section, success, error, info,
    prompt, prompt_int, prompt_float, prompt_password,
    format_minutes, clear,
)
from database.connection import get_db
from models import User, Subject, StudyPlan  # registers ORM models
from services.planner_service import PlannerService
from services.subject_service import SubjectService, SubjectValidationError


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
            error("Cannot connect to MySQL. Check your .env file and try again.")
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
        banner("Study Planner  ·  Welcome")
        print()
        print("  1. Register")
        print("  2. Login")
        print("  0. Exit")
        print()
        choice = prompt("Choose an option")

        if choice == "1":
            self._register()
        elif choice == "2":
            self._login()
        elif choice == "0":
            info("Goodbye! 👋")
            sys.exit(0)
        else:
            error("Invalid option.")

    def _register(self) -> None:
        section("Create Account")
        full_name      = prompt("Full name")
        email          = prompt("Email")
        password       = prompt_password("Password (min 6 chars)")
        confirm        = prompt_password("Confirm password")
        education_lvl  = prompt("Education level (e.g. Undergraduate)")
        course         = prompt("Course / Degree name")

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
                success(f"Account created! Welcome, {user.full_name}. Please log in.")
            except (AuthValidationError, DuplicateEmailError) as exc:
                error(str(exc))

    def _login(self) -> None:
        section("Login")
        email    = prompt("Email")
        password = prompt_password()

        with self._db.get_session() as session:
            try:
                user = self._auth_svc.login(session, email=email, password=password)
                # Detach so we can use the object outside the session
                session.expunge(user)
                self._current_user = user
                success(f"Welcome back, {user.full_name}!")
            except (AuthValidationError, InvalidCredentialsError) as exc:
                error(str(exc))

    # ======================================================================
    # App menu (logged in)
    # ======================================================================
    def _show_app_menu(self) -> None:
        assert self._current_user is not None
        banner(f"Study Planner  ·  {self._current_user.full_name}")
        print()
        print("  1. Add subject")
        print("  2. View my subjects")
        print("  3. Generate study plan")
        print("  4. View study plan")
        print("  5. Delete a subject")
        print("  6. Logout")
        print("  0. Exit")
        print()
        choice = prompt("Choose an option")

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
        section("Add Subject")
        name       = prompt("Subject name")
        difficulty = prompt_int("Difficulty", 1, 5)
        priority   = prompt_int("Priority", 1, 5)
        exam_date  = prompt("Exam date (YYYY-MM-DD)")

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
                success(f"Subject '{subj.name}' saved!")
            except SubjectValidationError as exc:
                error(str(exc))

    def _view_subjects(self) -> None:
        section("My Subjects")
        with self._db.get_session() as session:
            subjects = self._subject_svc.get_subjects_for_user(
                session, self._current_user.id  # type: ignore[union-attr]
            )

        if not subjects:
            info("No subjects yet. Add some first.")
            return

        print(
            f"\n  {'#':<4} {'Name':<25} {'Diff':>4} {'Prio':>4} {'Exam Date':>12}"
        )
        print("  " + "-" * 54)
        for i, s in enumerate(subjects, 1):
            print(
                f"  {i:<4} {s.name:<25} {s.difficulty:>4} {s.priority:>4} "
                f"{str(s.exam_date):>12}"
            )

    def _delete_subject(self) -> None:
        section("Delete Subject")
        with self._db.get_session() as session:
            subjects = self._subject_svc.get_subjects_for_user(
                session, self._current_user.id  # type: ignore[union-attr]
            )

        if not subjects:
            info("No subjects to delete.")
            return

        self._view_subjects()
        idx = prompt_int("Enter subject number to delete", 1, len(subjects))
        target = subjects[idx - 1]

        with self._db.get_session() as session:
            ok = self._subject_svc.delete_subject(
                session, target.id, self._current_user.id  # type: ignore[union-attr]
            )
        if ok:
            success(f"Subject '{target.name}' deleted.")
        else:
            error("Subject not found.")

    # ======================================================================
    # Study plan
    # ======================================================================
    def _generate_plan(self) -> None:
        section("Generate Study Plan")
        hours_per_day = prompt_float("Hours available per day", 0.5, 16)
        days_per_week = prompt_int("Days available per week", 1, 7)

        with self._db.get_session() as session:
            subjects = self._subject_svc.get_subjects_for_user(
                session, self._current_user.id  # type: ignore[union-attr]
            )
            if not subjects:
                error("Add subjects before generating a plan.")
                return

            try:
                plan = self._planner_svc.generate_and_save(
                    session,
                    user_id=self._current_user.id,  # type: ignore[union-attr]
                    subjects=subjects,
                    hours_per_day=hours_per_day,
                    days_per_week=days_per_week,
                )
                success("Study plan generated and saved!")
                self._print_plan(plan)
            except ValueError as exc:
                error(str(exc))

    def _view_plan(self) -> None:
        section("My Study Plan")
        with self._db.get_session() as session:
            plan = self._planner_svc.get_saved_plan(
                session, self._current_user.id  # type: ignore[union-attr]
            )

        if not plan:
            info("No study plan found. Generate one first.")
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
        info(f"Goodbye, {self._current_user.full_name}!")  # type: ignore[union-attr]
        self._current_user = None

    @staticmethod
    def _exit() -> None:
        info("Goodbye! 👋")
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
        info("Interrupted. Goodbye!")
        sys.exit(0)
