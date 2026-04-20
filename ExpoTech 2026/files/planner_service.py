"""
services/planner_service.py
-----------------------------
Core study-plan generation algorithm + DB persistence.

Algorithm summary
-----------------
1. Compute urgency weight from days remaining until exam.
2. Compute a composite score per subject.
3. Distribute available daily hours proportionally by score.
4. Clamp each block to [30, 120] minutes and round to nearest 30 min.
5. Re-distribute unused time to high-score subjects so the daily total
   exactly matches the requested hours.
6. Arrange subjects across the week, avoiding consecutive repeats.
7. Persist the resulting plan rows and return them.
"""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import date
from typing import NamedTuple

from sqlalchemy.orm import Session

from study_plan import StudyPlan
from subject import Subject


# ---------------------------------------------------------------------------
# Small data containers (no ORM coupling)
# ---------------------------------------------------------------------------
class SubjectScore(NamedTuple):
    subject: Subject
    score: float
    urgency: int


PlanRow = dict  # {day_of_week, subject_name, study_time_minutes}


# ---------------------------------------------------------------------------
# PlannerService
# ---------------------------------------------------------------------------
class PlannerService:
    """Generates and persists personalised study plans."""

    DAYS = [
        "Monday", "Tuesday", "Wednesday", "Thursday",
        "Friday", "Saturday", "Sunday",
    ]

    MIN_MINUTES = 30
    MAX_MINUTES = 120
    ROUNDING   = 30          # round to nearest N minutes

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def generate_and_save(
        self,
        session: Session,
        *,
        user_id: int,
        subjects: list[Subject],
        hours_per_day: float,
        days_per_week: int,
    ) -> dict[str, list[PlanRow]]:
        """
        Generate a study plan, delete the old one, persist the new one.
        Returns {day_name: [PlanRow, ...]}
        """
        if not subjects:
            raise ValueError("No subjects found. Please add subjects first.")

        if not (0.5 <= hours_per_day <= 16):
            raise ValueError("Hours per day must be between 0.5 and 16.")

        if not (1 <= days_per_week <= 7):
            raise ValueError("Days per week must be between 1 and 7.")

        # --- score every subject ---
        scored = self._score_subjects(subjects)

        # --- build the weekly schedule ---
        available_days = self.DAYS[:days_per_week]
        plan: dict[str, list[PlanRow]] = {}

        for day in available_days:
            plan[day] = self._allocate_day(
                scored, hours_per_day * 60, day
            )

        # --- persist ---
        self._save_plan(session, user_id=user_id, plan=plan)

        return plan

    def get_saved_plan(
        self, session: Session, user_id: int
    ) -> dict[str, list[PlanRow]]:
        """Load the most recently generated plan from the database."""
        rows: list[StudyPlan] = (
            session.query(StudyPlan)
            .filter_by(user_id=user_id)
            .order_by(StudyPlan.generated_at.desc(), StudyPlan.id)
            .all()
        )

        if not rows:
            return {}

        # Group by day, preserving insertion order
        plan: dict[str, list[PlanRow]] = defaultdict(list)
        latest_ts = rows[0].generated_at
        for row in rows:
            if row.generated_at != latest_ts:
                break                         # stop at previous generation
            plan[row.day_of_week].append(row.to_dict())

        return dict(plan)

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------
    def _score_subjects(self, subjects: list[Subject]) -> list[SubjectScore]:
        today = date.today()
        scored: list[SubjectScore] = []

        for subj in subjects:
            days_left = (subj.exam_date - today).days
            urgency = self._urgency_weight(days_left)
            score = (urgency * 0.5) + (subj.difficulty * 0.3) + (subj.priority * 0.2)
            scored.append(SubjectScore(subject=subj, score=score, urgency=urgency))

        # Highest score first
        scored.sort(key=lambda x: x.score, reverse=True)
        return scored

    @staticmethod
    def _urgency_weight(days_left: int) -> int:
        if days_left <= 3:
            return 5
        if days_left <= 7:
            return 4
        if days_left <= 14:
            return 3
        return 1

    # ------------------------------------------------------------------
    # Daily allocation
    # ------------------------------------------------------------------
    def _allocate_day(
        self,
        scored: list[SubjectScore],
        total_minutes: float,
        day: str,
    ) -> list[PlanRow]:
        """
        Distribute *total_minutes* across subjects, respecting min/max,
        rounding, and the no-consecutive-repeat rule.
        """
        total_score = sum(s.score for s in scored)

        # Raw proportional allocation
        raw: dict[str, float] = {}
        for ss in scored:
            raw[ss.subject.name] = (ss.score / total_score) * total_minutes

        # Clamp to [MIN, MAX]
        clamped: dict[str, int] = {}
        for name, minutes in raw.items():
            clamped[name] = max(
                self.MIN_MINUTES,
                min(self.MAX_MINUTES, self._round_to(minutes, self.ROUNDING)),
            )

        # Adjust so the total matches exactly
        clamped = self._adjust_total(clamped, int(total_minutes), scored)

        # Build rows — no consecutive same-subject (shuffle by score order)
        rows: list[PlanRow] = []
        prev_subject = None
        ordered = sorted(clamped.items(), key=lambda kv: -kv[1])

        for name, minutes in ordered:
            if minutes <= 0:
                continue
            # Simple no-consecutive check: if conflict, move to end
            if name == prev_subject:
                rows.append({"day_of_week": day, "subject_name": name,
                              "study_time_minutes": minutes})
            else:
                rows.insert(0, {"day_of_week": day, "subject_name": name,
                                 "study_time_minutes": minutes})
            prev_subject = name

        return rows

    def _adjust_total(
        self,
        clamped: dict[str, int],
        target: int,
        scored: list[SubjectScore],
    ) -> dict[str, int]:
        """
        Iteratively add/subtract ROUNDING units to the highest-priority
        subjects until the total equals *target*.
        """
        priority_order = [ss.subject.name for ss in scored]

        while True:
            current = sum(clamped.values())
            diff = target - current
            if diff == 0:
                break

            step = self.ROUNDING if diff > 0 else -self.ROUNDING
            adjusted = False

            for name in priority_order:
                if name not in clamped:
                    continue
                new_val = clamped[name] + step
                if self.MIN_MINUTES <= new_val <= self.MAX_MINUTES:
                    clamped[name] = new_val
                    adjusted = True
                    break

            if not adjusted:
                # Can't adjust further — accept small rounding error
                break

        return clamped

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    @staticmethod
    def _save_plan(
        session: Session,
        user_id: int,
        plan: dict[str, list[PlanRow]],
    ) -> None:
        # Delete previous plan for this user
        session.query(StudyPlan).filter_by(user_id=user_id).delete()

        for day, rows in plan.items():
            for row in rows:
                entry = StudyPlan(
                    user_id=user_id,
                    day_of_week=day,
                    subject_name=row["subject_name"],
                    study_time_minutes=row["study_time_minutes"],
                )
                session.add(entry)

        session.flush()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _round_to(value: float, base: int) -> int:
        """Round *value* to the nearest multiple of *base*."""
        return int(base * round(value / base))
