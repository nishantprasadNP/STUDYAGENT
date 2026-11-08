"""Prove the Alembic migration produces the schema and constraints we rely on."""

from datetime import date, datetime

import pytest
from alembic import command
from sqlalchemy import Engine, inspect, text
from sqlalchemy.exc import IntegrityError, StatementError
from sqlalchemy.orm import Session

from app.models import Notification, StudentProfile, StudyPlan, StudySession, Task, Topic
from app.models.enums import NotificationType, PlanStatus, SessionSource
from tests.conftest import alembic_config

EXPECTED_TABLES = {
    "agent_messages",
    "checkin_task_entries",
    "daily_checkins",
    "learning_patterns",
    "notifications",
    "revision_changes",
    "schedule_revisions",
    "settings",
    "student_profile",
    "study_plans",
    "study_sessions",
    "tasks",
    "topic_prerequisites",
    "topics",
    "weekly_reports",
}


def _topic(session: Session) -> Topic:
    topic = Topic(
        slug="arrays",
        name="Arrays",
        category="linear",
        order_index=1,
        default_problem_count=10,
        est_minutes_per_problem=20,
        difficulty_tier=1,
    )
    session.add(topic)
    session.flush()
    return topic


def _plan(session: Session, status: PlanStatus = PlanStatus.ACTIVE) -> StudyPlan:
    plan = StudyPlan(status=status, start_date=date(2026, 1, 1), end_date=date(2026, 3, 1))
    session.add(plan)
    session.flush()
    return plan


def test_all_tables_exist(engine: Engine) -> None:
    tables = set(inspect(engine).get_table_names())
    assert tables >= EXPECTED_TABLES
    assert tables - EXPECTED_TABLES == {"alembic_version"}


def test_sqlite_pragmas(engine: Engine) -> None:
    with engine.connect() as conn:
        assert conn.execute(text("PRAGMA foreign_keys")).scalar() == 1
        assert conn.execute(text("PRAGMA journal_mode")).scalar() == "wal"


def test_student_profile_is_single_row(db_session: Session) -> None:
    db_session.add(StudentProfile(id=1, name="A", timezone="Asia/Kolkata"))
    db_session.flush()
    db_session.add(StudentProfile(id=2, name="B", timezone="Asia/Kolkata"))
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_only_one_active_plan(db_session: Session) -> None:
    _plan(db_session, PlanStatus.ACTIVE)
    _plan(db_session, PlanStatus.ARCHIVED)  # allowed alongside an active plan
    with pytest.raises(IntegrityError):
        _plan(db_session, PlanStatus.ACTIVE)


def test_task_completed_cannot_exceed_planned(db_session: Session) -> None:
    topic = _topic(db_session)
    plan = _plan(db_session)
    db_session.add(
        Task(
            plan_id=plan.id,
            topic_id=topic.id,
            scheduled_date=date(2026, 1, 2),
            title="Arrays",
            planned_problems=3,
            completed_problems=4,
            planned_minutes=60,
        )
    )
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_session_solved_cannot_exceed_attempted(db_session: Session) -> None:
    topic = _topic(db_session)
    db_session.add(
        StudySession(
            date=date(2026, 1, 2),
            topic_id=topic.id,
            duration_minutes=30,
            problems_attempted=2,
            problems_solved=3,
            source=SessionSource.MANUAL,
        )
    )
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_naive_datetime_rejected(db_session: Session) -> None:
    db_session.add(
        Notification(type=NotificationType.WEEKLY_REPORT, read_at=datetime(2026, 1, 1, 12, 0))
    )
    with pytest.raises(StatementError) as exc_info:
        db_session.flush()
    assert isinstance(exc_info.value.orig, ValueError)


def test_downgrade_then_upgrade(engine: Engine, db_url: str) -> None:
    cfg = alembic_config(db_url)
    command.downgrade(cfg, "base")
    assert set(inspect(engine).get_table_names()) == {"alembic_version"}
    command.upgrade(cfg, "head")
    assert set(inspect(engine).get_table_names()) >= EXPECTED_TABLES
