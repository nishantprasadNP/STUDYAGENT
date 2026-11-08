"""initial schema

All 15 tables. Reviewed by hand: UTCDateTime -> sa.DateTime (stored as naive UTC),
enum CHECKs come from sa.Enum(create_constraint=True), partial unique index on
study_plans.status, and every table-level CHECK constraint.

TODO(phase-1+): batch_alter_table on SQLite recreates tables; pass the Enum types
(or table_args) explicitly so enum CHECK constraints survive later migrations.

Revision ID: 0001
Revises:
Create Date: 2026-11-08 12:08:38.730956

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agent_messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "role",
            sa.Enum(
                "user",
                "assistant",
                "tool",
                name="messagerole",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("tool_name", sa.String(length=64), nullable=True),
        sa.Column("tool_args", sa.JSON(), nullable=True),
        sa.Column("tool_result", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_agent_messages")),
    )
    with op.batch_alter_table("agent_messages", schema=None) as batch_op:
        batch_op.create_index("ix_agent_messages_created_at", ["created_at"], unique=False)

    op.create_table(
        "daily_checkins",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "reminded",
                "completed",
                "unreported",
                name="checkinstatus",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("total_minutes", sa.Integer(), nullable=True),
        sa.Column(
            "overall_difficulty",
            sa.Enum(
                "easy",
                "moderate",
                "difficult",
                name="difficulty",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=True,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("completion_rate", sa.Float(), nullable=True),
        sa.Column(
            "decision",
            sa.Enum(
                "on_track",
                "behind",
                "ahead",
                "no_data",
                name="checkindecision",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=True,
        ),
        sa.Column("prompted_at", sa.DateTime(), nullable=True),
        sa.Column("reminded_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "completion_rate IS NULL OR (completion_rate >= 0 AND completion_rate <= 1)",
            name=op.f("ck_daily_checkins_completion_rate_range"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_daily_checkins")),
        sa.UniqueConstraint("date", name=op.f("uq_daily_checkins_date")),
    )
    op.create_table(
        "learning_patterns",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("pattern_key", sa.String(length=64), nullable=False),
        sa.Column("value", sa.JSON(), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("computed_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_learning_patterns")),
        sa.UniqueConstraint("pattern_key", name=op.f("uq_learning_patterns_pattern_key")),
    )
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "type",
            sa.Enum(
                "checkin_due",
                "checkin_reminder",
                "revision_proposed",
                "weekly_report",
                name="notificationtype",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("read_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_notifications")),
    )
    with op.batch_alter_table("notifications", schema=None) as batch_op:
        batch_op.create_index("ix_notifications_read_at", ["read_at"], unique=False)

    op.create_table(
        "settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "behind_completion_threshold",
            sa.Float(),
            server_default=sa.text("0.70"),
            nullable=False,
        ),
        sa.Column(
            "behind_carryover_count", sa.Integer(), server_default=sa.text("2"), nullable=False
        ),
        sa.Column(
            "ahead_completion_threshold", sa.Float(), server_default=sa.text("1.00"), nullable=False
        ),
        sa.Column(
            "weak_topic_min_problems", sa.Integer(), server_default=sa.text("5"), nullable=False
        ),
        sa.Column(
            "weak_topic_solve_ratio", sa.Float(), server_default=sa.text("0.60"), nullable=False
        ),
        sa.Column(
            "weak_topic_difficult_ratio", sa.Float(), server_default=sa.text("0.50"), nullable=False
        ),
        sa.Column(
            "max_daily_overbook_ratio", sa.Float(), server_default=sa.text("1.00"), nullable=False
        ),
        sa.Column(
            "revision_expiry_hours", sa.Integer(), server_default=sa.text("24"), nullable=False
        ),
        sa.Column("max_topics_per_day", sa.Integer(), server_default=sa.text("2"), nullable=False),
        sa.Column(
            "outstanding_checkin_days", sa.Integer(), server_default=sa.text("3"), nullable=False
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("id = 1", name=op.f("ck_settings_single_row")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_settings")),
    )
    op.create_table(
        "student_profile",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("goal_text", sa.Text(), nullable=True),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column(
            "skill_level",
            sa.Enum(
                "beginner",
                "intermediate",
                "advanced",
                name="skilllevel",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=True,
        ),
        sa.Column("weekly_availability", sa.JSON(), nullable=False),
        sa.Column("preferred_session_minutes", sa.Integer(), nullable=True),
        sa.Column("checkin_time", sa.String(length=5), nullable=False),
        sa.Column("reminder_time", sa.String(length=5), nullable=False),
        sa.Column("preferences", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("id = 1", name=op.f("ck_student_profile_single_row")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_student_profile")),
    )
    op.create_table(
        "study_plans",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "draft",
                "active",
                "superseded",
                "archived",
                name="planstatus",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("end_date >= start_date", name=op.f("ck_study_plans_date_range")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_study_plans")),
    )
    with op.batch_alter_table("study_plans", schema=None) as batch_op:
        batch_op.create_index(
            "uq_study_plans_one_active",
            ["status"],
            unique=True,
            sqlite_where=sa.text("status = 'active'"),
        )

    op.create_table(
        "topics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("default_problem_count", sa.Integer(), nullable=False),
        sa.Column("est_minutes_per_problem", sa.Integer(), nullable=False),
        sa.Column("difficulty_tier", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "difficulty_tier BETWEEN 1 AND 3", name=op.f("ck_topics_difficulty_tier")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_topics")),
        sa.UniqueConstraint("slug", name=op.f("uq_topics_slug")),
    )
    op.create_table(
        "weekly_reports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("week_start", sa.Date(), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("summary_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_weekly_reports")),
        sa.UniqueConstraint("week_start", name=op.f("uq_weekly_reports_week_start")),
    )
    op.create_table(
        "schedule_revisions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("base_plan_version", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "proposed",
                "approved",
                "applied",
                "rejected",
                "expired",
                name="revisionstatus",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column(
            "trigger",
            sa.Enum(
                "checkin",
                "user_request",
                "chat",
                name="revisiontrigger",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("validation", sa.JSON(), nullable=False),
        sa.Column("presented_at", sa.DateTime(), nullable=True),
        sa.Column("decided_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["plan_id"], ["study_plans.id"], name=op.f("fk_schedule_revisions_plan_id_study_plans")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_schedule_revisions")),
    )
    with op.batch_alter_table("schedule_revisions", schema=None) as batch_op:
        batch_op.create_index("ix_schedule_revisions_status", ["status"], unique=False)

    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("topic_id", sa.Integer(), nullable=False),
        sa.Column("scheduled_date", sa.Date(), nullable=False),
        sa.Column("order_in_day", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("planned_problems", sa.Integer(), nullable=False),
        sa.Column("completed_problems", sa.Integer(), nullable=False),
        sa.Column("planned_minutes", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "in_progress",
                "partial",
                "completed",
                "skipped",
                name="taskstatus",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("carried_from_task_id", sa.Integer(), nullable=True),
        sa.Column("created_by_revision_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "completed_problems BETWEEN 0 AND planned_problems",
            name=op.f("ck_tasks_completed_problems_range"),
        ),
        sa.CheckConstraint("planned_minutes > 0", name=op.f("ck_tasks_planned_minutes_positive")),
        sa.CheckConstraint("planned_problems > 0", name=op.f("ck_tasks_planned_problems_positive")),
        sa.ForeignKeyConstraint(
            ["carried_from_task_id"], ["tasks.id"], name=op.f("fk_tasks_carried_from_task_id_tasks")
        ),
        sa.ForeignKeyConstraint(
            ["created_by_revision_id"],
            ["schedule_revisions.id"],
            name=op.f("fk_tasks_created_by_revision_id_schedule_revisions"),
        ),
        sa.ForeignKeyConstraint(
            ["plan_id"], ["study_plans.id"], name=op.f("fk_tasks_plan_id_study_plans")
        ),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], name=op.f("fk_tasks_topic_id_topics")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tasks")),
    )
    with op.batch_alter_table("tasks", schema=None) as batch_op:
        batch_op.create_index(
            "ix_tasks_plan_id_scheduled_date", ["plan_id", "scheduled_date"], unique=False
        )
        batch_op.create_index("ix_tasks_scheduled_date", ["scheduled_date"], unique=False)

    op.create_table(
        "topic_prerequisites",
        sa.Column("topic_id", sa.Integer(), nullable=False),
        sa.Column("prerequisite_topic_id", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "topic_id != prerequisite_topic_id", name=op.f("ck_topic_prerequisites_not_self")
        ),
        sa.ForeignKeyConstraint(
            ["prerequisite_topic_id"],
            ["topics.id"],
            name=op.f("fk_topic_prerequisites_prerequisite_topic_id_topics"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["topic_id"],
            ["topics.id"],
            name=op.f("fk_topic_prerequisites_topic_id_topics"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "topic_id", "prerequisite_topic_id", name=op.f("pk_topic_prerequisites")
        ),
    )
    op.create_table(
        "checkin_task_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("checkin_id", sa.Integer(), nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("reported_completed_problems", sa.Integer(), nullable=False),
        sa.Column(
            "reported_status",
            sa.Enum(
                "pending",
                "in_progress",
                "partial",
                "completed",
                "skipped",
                name="taskstatus",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "reported_completed_problems >= 0", name=op.f("ck_checkin_task_entries_reported_nonneg")
        ),
        sa.ForeignKeyConstraint(
            ["checkin_id"],
            ["daily_checkins.id"],
            name=op.f("fk_checkin_task_entries_checkin_id_daily_checkins"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["task_id"], ["tasks.id"], name=op.f("fk_checkin_task_entries_task_id_tasks")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_checkin_task_entries")),
        sa.UniqueConstraint(
            "checkin_id", "task_id", name=op.f("uq_checkin_task_entries_checkin_id_task_id")
        ),
    )
    op.create_table(
        "revision_changes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("revision_id", sa.Integer(), nullable=False),
        sa.Column(
            "change_type",
            sa.Enum(
                "move",
                "resize",
                "add",
                "remove",
                name="changetype",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("task_id", sa.Integer(), nullable=True),
        sa.Column("topic_id", sa.Integer(), nullable=False),
        sa.Column("from_date", sa.Date(), nullable=True),
        sa.Column("to_date", sa.Date(), nullable=True),
        sa.Column("from_problems", sa.Integer(), nullable=True),
        sa.Column("to_problems", sa.Integer(), nullable=True),
        sa.Column("from_minutes", sa.Integer(), nullable=True),
        sa.Column("to_minutes", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["revision_id"],
            ["schedule_revisions.id"],
            name=op.f("fk_revision_changes_revision_id_schedule_revisions"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["task_id"], ["tasks.id"], name=op.f("fk_revision_changes_task_id_tasks")
        ),
        sa.ForeignKeyConstraint(
            ["topic_id"], ["topics.id"], name=op.f("fk_revision_changes_topic_id_topics")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_revision_changes")),
    )
    op.create_table(
        "study_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("topic_id", sa.Integer(), nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("problems_attempted", sa.Integer(), nullable=False),
        sa.Column("problems_solved", sa.Integer(), nullable=False),
        sa.Column(
            "difficulty",
            sa.Enum(
                "easy",
                "moderate",
                "difficult",
                name="difficulty",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=True,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "source",
            sa.Enum(
                "manual",
                "checkin",
                "chat",
                name="sessionsource",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "duration_minutes BETWEEN 1 AND 720", name=op.f("ck_study_sessions_duration_range")
        ),
        sa.CheckConstraint(
            "problems_attempted >= 0", name=op.f("ck_study_sessions_attempted_nonneg")
        ),
        sa.CheckConstraint(
            "problems_solved <= problems_attempted",
            name=op.f("ck_study_sessions_solved_le_attempted"),
        ),
        sa.CheckConstraint("problems_solved >= 0", name=op.f("ck_study_sessions_solved_nonneg")),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["tasks.id"],
            name=op.f("fk_study_sessions_task_id_tasks"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["topic_id"], ["topics.id"], name=op.f("fk_study_sessions_topic_id_topics")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_study_sessions")),
    )
    with op.batch_alter_table("study_sessions", schema=None) as batch_op:
        batch_op.create_index("ix_study_sessions_date", ["date"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("study_sessions", schema=None) as batch_op:
        batch_op.drop_index("ix_study_sessions_date")

    op.drop_table("study_sessions")
    op.drop_table("revision_changes")
    op.drop_table("checkin_task_entries")
    op.drop_table("topic_prerequisites")
    with op.batch_alter_table("tasks", schema=None) as batch_op:
        batch_op.drop_index("ix_tasks_scheduled_date")
        batch_op.drop_index("ix_tasks_plan_id_scheduled_date")

    op.drop_table("tasks")
    with op.batch_alter_table("schedule_revisions", schema=None) as batch_op:
        batch_op.drop_index("ix_schedule_revisions_status")

    op.drop_table("schedule_revisions")
    op.drop_table("weekly_reports")
    op.drop_table("topics")
    with op.batch_alter_table("study_plans", schema=None) as batch_op:
        batch_op.drop_index("uq_study_plans_one_active", sqlite_where=sa.text("status = 'active'"))

    op.drop_table("study_plans")
    op.drop_table("student_profile")
    op.drop_table("settings")
    with op.batch_alter_table("notifications", schema=None) as batch_op:
        batch_op.drop_index("ix_notifications_read_at")

    op.drop_table("notifications")
    op.drop_table("learning_patterns")
    op.drop_table("daily_checkins")
    with op.batch_alter_table("agent_messages", schema=None) as batch_op:
        batch_op.drop_index("ix_agent_messages_created_at")

    op.drop_table("agent_messages")
