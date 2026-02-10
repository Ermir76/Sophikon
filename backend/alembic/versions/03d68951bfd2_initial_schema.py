"""initial schema

Revision ID: 03d68951bfd2
Revises:
Create Date: 2026-02-09 01:35:26.324177

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "03d68951bfd2"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # === Tier 0: No dependencies ===
    op.create_table(
        "role",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "permissions",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
            comment="Permission array: ['resource:action']",
        ),
        sa.Column(
            "is_system",
            sa.Boolean(),
            server_default=sa.text("FALSE"),
            nullable=False,
            comment="System roles cannot be modified/deleted",
        ),
        sa.Column(
            "scope",
            sa.String(length=20),
            server_default=sa.text("'project'"),
            nullable=False,
            comment="'system' or 'project'",
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "scope IN ('system', 'project')", name="check_role_scope_valid"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_role_name"), "role", ["name"], unique=True)

    # === Tier 1: Depends on role ===
    op.create_table(
        "user",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column(
            "password_hash",
            sa.String(length=255),
            nullable=True,
            comment="bcrypt hash, NULL for OAuth users",
        ),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("avatar_url", sa.String(length=500), nullable=True),
        sa.Column("system_role_id", sa.UUID(), nullable=False),
        sa.Column(
            "oauth_provider",
            sa.String(length=50),
            nullable=True,
            comment="OAuth provider: 'google', 'github', etc.",
        ),
        sa.Column(
            "oauth_id",
            sa.String(length=255),
            nullable=True,
            comment="Provider's user ID",
        ),
        sa.Column(
            "is_active", sa.Boolean(), server_default=sa.text("TRUE"), nullable=False
        ),
        sa.Column(
            "email_verified",
            sa.Boolean(),
            server_default=sa.text("FALSE"),
            nullable=False,
        ),
        sa.Column(
            "preferences",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
            comment="User settings: theme, notifications, etc.",
        ),
        sa.Column(
            "timezone",
            sa.String(length=50),
            server_default=sa.text("'UTC'"),
            nullable=False,
        ),
        sa.Column(
            "locale",
            sa.String(length=10),
            server_default=sa.text("'en-US'"),
            nullable=False,
        ),
        sa.Column("last_login_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["system_role_id"],
            ["role.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_user_oauth",
        "user",
        ["oauth_provider", "oauth_id"],
        unique=True,
        postgresql_where=sa.text("oauth_provider IS NOT NULL"),
    )
    op.create_index(op.f("ix_user_email"), "user", ["email"], unique=True)

    # === Tier 2: calendar <-> project circular dependency ===
    # Create calendar without project FK first
    op.create_table(
        "calendar",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "project_id", sa.UUID(), nullable=True, comment="NULL = global calendar"
        ),
        sa.Column(
            "base_calendar_id",
            sa.UUID(),
            nullable=True,
            comment="Parent calendar for inheritance",
        ),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column(
            "is_base",
            sa.Boolean(),
            server_default=sa.text("FALSE"),
            nullable=False,
            comment="Is this a base/template calendar?",
        ),
        sa.Column(
            "work_week",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text(
                '\'[\n            null,\n            {"start": "09:00", "end": "17:00", "breaks": [{"start": "12:00", "end": "13:00"}]},\n            {"start": "09:00", "end": "17:00", "breaks": [{"start": "12:00", "end": "13:00"}]},\n            {"start": "09:00", "end": "17:00", "breaks": [{"start": "12:00", "end": "13:00"}]},\n            {"start": "09:00", "end": "17:00", "breaks": [{"start": "12:00", "end": "13:00"}]},\n            {"start": "09:00", "end": "17:00", "breaks": [{"start": "12:00", "end": "13:00"}]},\n            null\n        ]\'::jsonb'
            ),
            nullable=False,
            comment="7-day work pattern (Sunday=0)",
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["base_calendar_id"], ["calendar.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_calendar_project", "calendar", ["project_id"], unique=False)
    op.create_index(
        op.f("ix_calendar_project_id"), "calendar", ["project_id"], unique=False
    )

    # Create project (depends on user, calendar)
    op.create_table(
        "project",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("owner_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("finish_date", sa.Date(), nullable=True),
        sa.Column("status_date", sa.Date(), nullable=True),
        sa.Column(
            "schedule_from",
            sa.String(length=20),
            server_default=sa.text("'START'"),
            nullable=False,
            comment="'start' or 'finish'",
        ),
        sa.Column("default_calendar_id", sa.UUID(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default=sa.text("'PLANNING'"),
            nullable=False,
            comment="'planning', 'active', 'on_hold', 'completed', 'cancelled'",
        ),
        sa.Column("budget", sa.DECIMAL(precision=15, scale=2), nullable=True),
        sa.Column(
            "currency",
            sa.String(length=3),
            server_default=sa.text("'USD'"),
            nullable=False,
        ),
        sa.Column(
            "settings",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text(
                '\'{\n        "hours_per_day": 8,\n        "hours_per_week": 40,\n        "days_per_month": 20,\n        "first_day_of_week": 1,\n        "default_task_type": "FIXED_UNITS",\n        "new_tasks_effort_driven": true,\n        "auto_calculate": true\n        }\'::jsonb'
            ),
            nullable=False,
        ),
        sa.Column(
            "is_deleted", sa.Boolean(), server_default=sa.text("FALSE"), nullable=False
        ),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "schedule_from IN ('START', 'FINISH')", name="check_project_schedule_from"
        ),
        sa.CheckConstraint(
            "status IN ('PLANNING', 'ACTIVE', 'ON_HOLD', 'COMPLETED', 'CANCELLED')",
            name="check_project_status",
        ),
        sa.ForeignKeyConstraint(
            ["default_calendar_id"], ["calendar.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["owner_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_project_owner",
        "project",
        ["owner_id"],
        unique=False,
        postgresql_where=sa.text("NOT is_deleted"),
    )
    op.create_index(
        "idx_project_status",
        "project",
        ["status"],
        unique=False,
        postgresql_where=sa.text("NOT is_deleted"),
    )
    op.create_index(op.f("ix_project_owner_id"), "project", ["owner_id"], unique=False)

    # Now add the deferred FK: calendar.project_id -> project.id
    op.create_foreign_key(
        "fk_calendar_project_id",
        "calendar",
        "project",
        ["project_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # === Tier 3: Depends on calendar/project ===
    op.create_table(
        "calendar_exception",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("calendar_id", sa.UUID(), nullable=False),
        sa.Column(
            "name",
            sa.String(length=100),
            nullable=False,
            comment="Exception name (e.g., 'Christmas')",
        ),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column(
            "is_working",
            sa.Boolean(),
            server_default=sa.text("FALSE"),
            nullable=False,
            comment="Is this a working exception?",
        ),
        sa.Column(
            "work_times",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="Custom hours if is_working=TRUE",
        ),
        sa.Column(
            "recurrence",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="Recurrence pattern (e.g., {'type': 'yearly', 'month': 12, 'day': 25})",
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["calendar_id"], ["calendar.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_calendar_exception_calendar",
        "calendar_exception",
        ["calendar_id"],
        unique=False,
    )
    op.create_index(
        "idx_calendar_exception_dates",
        "calendar_exception",
        ["calendar_id", "start_date", "end_date"],
        unique=False,
    )
    op.create_index(
        op.f("ix_calendar_exception_calendar_id"),
        "calendar_exception",
        ["calendar_id"],
        unique=False,
    )

    op.create_table(
        "task",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("parent_task_id", sa.UUID(), nullable=True),
        sa.Column("wbs_code", sa.String(length=50), nullable=False),
        sa.Column(
            "outline_level", sa.Integer(), server_default=sa.text("1"), nullable=False
        ),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=500), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "is_milestone",
            sa.Boolean(),
            server_default=sa.text("FALSE"),
            nullable=False,
        ),
        sa.Column(
            "is_summary", sa.Boolean(), server_default=sa.text("FALSE"), nullable=False
        ),
        sa.Column(
            "is_critical", sa.Boolean(), server_default=sa.text("FALSE"), nullable=False
        ),
        sa.Column("calendar_id", sa.UUID(), nullable=True),
        sa.Column(
            "duration", sa.Integer(), server_default=sa.text("480"), nullable=False
        ),
        sa.Column("work", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "actual_duration", sa.Integer(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column(
            "actual_work", sa.Integer(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column(
            "remaining_duration",
            sa.Integer(),
            server_default=sa.text("480"),
            nullable=False,
        ),
        sa.Column(
            "remaining_work", sa.Integer(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("finish_date", sa.Date(), nullable=False),
        sa.Column("actual_start", sa.Date(), nullable=True),
        sa.Column("actual_finish", sa.Date(), nullable=True),
        sa.Column(
            "percent_complete",
            sa.DECIMAL(precision=5, scale=2),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "percent_work_complete",
            sa.DECIMAL(precision=5, scale=2),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "task_type",
            sa.String(length=20),
            server_default=sa.text("'FIXED_UNITS'"),
            nullable=False,
        ),
        sa.Column(
            "effort_driven",
            sa.Boolean(),
            server_default=sa.text("TRUE"),
            nullable=False,
        ),
        sa.Column(
            "constraint_type",
            sa.String(length=10),
            server_default=sa.text("'ASAP'"),
            nullable=False,
        ),
        sa.Column("constraint_date", sa.Date(), nullable=True),
        sa.Column("deadline", sa.Date(), nullable=True),
        sa.Column(
            "total_slack", sa.Integer(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column(
            "free_slack", sa.Integer(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column(
            "priority", sa.Integer(), server_default=sa.text("500"), nullable=False
        ),
        sa.Column(
            "fixed_cost",
            sa.DECIMAL(precision=15, scale=2),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "fixed_cost_accrual",
            sa.String(length=10),
            server_default=sa.text("'PRORATED'"),
            nullable=False,
        ),
        sa.Column(
            "total_cost",
            sa.DECIMAL(precision=15, scale=2),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "actual_cost",
            sa.DECIMAL(precision=15, scale=2),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "remaining_cost",
            sa.DECIMAL(precision=15, scale=2),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "bcws",
            sa.DECIMAL(precision=15, scale=2),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "bcwp",
            sa.DECIMAL(precision=15, scale=2),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "acwp",
            sa.DECIMAL(precision=15, scale=2),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column("external_id", sa.String(length=100), nullable=True),
        sa.Column(
            "is_deleted", sa.Boolean(), server_default=sa.text("FALSE"), nullable=False
        ),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "constraint_type IN ('ASAP', 'ALAP', 'MSO', 'MFO', 'SNET', 'SNLT', 'FNET', 'FNLT')",
            name="check_task_constraint_type",
        ),
        sa.CheckConstraint(
            "fixed_cost_accrual IN ('START', 'END', 'PRORATED')",
            name="check_task_fixed_cost_accrual",
        ),
        sa.CheckConstraint(
            "task_type IN ('FIXED_UNITS', 'FIXED_DURATION', 'FIXED_WORK')",
            name="check_task_type",
        ),
        sa.CheckConstraint(
            "percent_complete >= 0 AND percent_complete <= 100",
            name="check_task_percent_complete",
        ),
        sa.CheckConstraint(
            "percent_work_complete >= 0 AND percent_work_complete <= 100",
            name="check_task_percent_work_complete",
        ),
        sa.CheckConstraint(
            "priority >= 0 AND priority <= 1000", name="check_task_priority"
        ),
        sa.ForeignKeyConstraint(
            ["calendar_id"],
            ["calendar.id"],
        ),
        sa.ForeignKeyConstraint(
            ["parent_task_id"],
            ["task.id"],
        ),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_task_dates",
        "task",
        ["project_id", "start_date", "finish_date"],
        unique=False,
        postgresql_where=sa.text("NOT is_deleted"),
    )
    op.create_index(
        "idx_task_parent",
        "task",
        ["parent_task_id"],
        unique=False,
        postgresql_where=sa.text("NOT is_deleted"),
    )
    op.create_index(
        "idx_task_project",
        "task",
        ["project_id"],
        unique=False,
        postgresql_where=sa.text("NOT is_deleted"),
    )
    op.create_index(
        "idx_task_project_order",
        "task",
        ["project_id", "order_index"],
        unique=False,
        postgresql_where=sa.text("NOT is_deleted"),
    )
    op.create_index(
        "idx_task_project_wbs",
        "task",
        ["project_id", "wbs_code"],
        unique=False,
        postgresql_where=sa.text("NOT is_deleted"),
    )
    op.create_index(op.f("ix_task_project_id"), "task", ["project_id"], unique=False)

    # === Tier 4: Depends on project + user ===
    op.create_table(
        "activity_log",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=True),
        sa.Column("user_id", sa.UUID(), nullable=True, comment="Actor"),
        sa.Column(
            "action",
            sa.String(length=50),
            nullable=False,
            comment="Action (created, updated, deleted, restored)",
        ),
        sa.Column(
            "entity_type",
            sa.String(length=50),
            nullable=False,
            comment="Entity type (task, resource, etc.)",
        ),
        sa.Column("entity_id", sa.UUID(), nullable=True),
        sa.Column(
            "entity_name",
            sa.String(length=500),
            nullable=True,
            comment="Entity name (for display after delete)",
        ),
        sa.Column(
            "changes",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="What changed (for updates)",
        ),
        sa.Column("ip_address", postgresql.INET(), nullable=True, comment="Client IP"),
        sa.Column(
            "user_agent", sa.String(length=500), nullable=True, comment="Browser/client"
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Action timestamp",
        ),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_activity_log_entity",
        "activity_log",
        ["entity_type", "entity_id"],
        unique=False,
    )
    op.create_index(
        "idx_activity_log_project",
        "activity_log",
        ["project_id", sa.literal_column("created_at DESC")],
        unique=False,
        postgresql_where=sa.text("project_id IS NOT NULL"),
    )
    op.create_index(
        "idx_activity_log_user",
        "activity_log",
        ["user_id", sa.literal_column("created_at DESC")],
        unique=False,
    )

    op.create_table(
        "ai_conversation",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False, comment="Project context"),
        sa.Column("user_id", sa.UUID(), nullable=False, comment="Conversation owner"),
        sa.Column(
            "title",
            sa.String(length=255),
            nullable=True,
            comment="Conversation title (auto or user-set)",
        ),
        sa.Column(
            "context_snapshot",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="Cached context (optional)",
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_ai_conversation_project", "ai_conversation", ["project_id"], unique=False
    )
    op.create_index(
        "idx_ai_conversation_user", "ai_conversation", ["user_id"], unique=False
    )
    op.create_index(
        op.f("ix_ai_conversation_project_id"),
        "ai_conversation",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_ai_conversation_user_id"), "ai_conversation", ["user_id"], unique=False
    )

    op.create_table(
        "ai_usage",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column(
            "feature",
            sa.String(length=50),
            nullable=False,
            comment="Feature (chat, estimation, suggestion)",
        ),
        sa.Column("model", sa.String(length=100), nullable=False, comment="Model used"),
        sa.Column(
            "tokens_in",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
            comment="Input tokens",
        ),
        sa.Column(
            "tokens_out",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
            comment="Output tokens",
        ),
        sa.Column(
            "estimated_cost",
            sa.DECIMAL(precision=10, scale=6),
            server_default=sa.text("0"),
            nullable=False,
            comment="Estimated cost in USD",
        ),
        sa.Column("usage_date", sa.Date(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_ai_usage_date", "ai_usage", ["usage_date"], unique=False)
    op.create_index(
        "idx_ai_usage_user_date", "ai_usage", ["user_id", "usage_date"], unique=False
    )

    op.create_table(
        "attachment",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "entity_type",
            sa.String(length=50),
            nullable=False,
            comment="Entity type (task, project, comment)",
        ),
        sa.Column(
            "entity_id", sa.UUID(), nullable=False, comment="Entity ID (polymorphic)"
        ),
        sa.Column("uploaded_by_id", sa.UUID(), nullable=False),
        sa.Column(
            "file_name",
            sa.String(length=255),
            nullable=False,
            comment="Original filename",
        ),
        sa.Column(
            "file_size", sa.BigInteger(), nullable=False, comment="Size in bytes"
        ),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column(
            "storage_path",
            sa.String(length=500),
            nullable=False,
            comment="S3 path or local path",
        ),
        sa.Column(
            "storage_provider",
            sa.String(length=20),
            server_default=sa.text("'local'"),
            nullable=False,
        ),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "is_deleted", sa.Boolean(), server_default=sa.text("FALSE"), nullable=False
        ),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Upload timestamp",
        ),
        sa.ForeignKeyConstraint(
            ["uploaded_by_id"],
            ["user.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_attachment_entity",
        "attachment",
        ["entity_type", "entity_id"],
        unique=False,
        postgresql_where=sa.text("NOT is_deleted"),
    )

    op.create_table(
        "comment",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "entity_type",
            sa.String(length=50),
            nullable=False,
            comment="Entity type (task, project)",
        ),
        sa.Column(
            "entity_id", sa.UUID(), nullable=False, comment="Entity ID (polymorphic)"
        ),
        sa.Column("author_id", sa.UUID(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("parent_comment_id", sa.UUID(), nullable=True),
        sa.Column(
            "mentions",
            postgresql.ARRAY(sa.UUID()),
            server_default=sa.text("'{}'"),
            nullable=False,
            comment="Array of mentioned user IDs",
        ),
        sa.Column(
            "is_edited", sa.Boolean(), server_default=sa.text("FALSE"), nullable=False
        ),
        sa.Column("edited_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "is_deleted", sa.Boolean(), server_default=sa.text("FALSE"), nullable=False
        ),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["author_id"],
            ["user.id"],
        ),
        sa.ForeignKeyConstraint(
            ["parent_comment_id"], ["comment.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_comment_author",
        "comment",
        ["author_id"],
        unique=False,
        postgresql_where=sa.text("NOT is_deleted"),
    )
    op.create_index(
        "idx_comment_entity",
        "comment",
        ["entity_type", "entity_id"],
        unique=False,
        postgresql_where=sa.text("NOT is_deleted"),
    )
    op.create_index(
        "idx_comment_parent",
        "comment",
        ["parent_comment_id"],
        unique=False,
        postgresql_where=sa.text("parent_comment_id IS NOT NULL"),
    )
    op.create_index(
        op.f("ix_comment_author_id"), "comment", ["author_id"], unique=False
    )
    op.create_index(
        op.f("ix_comment_parent_comment_id"),
        "comment",
        ["parent_comment_id"],
        unique=False,
    )

    op.create_table(
        "dependency",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("predecessor_id", sa.UUID(), nullable=False),
        sa.Column("successor_id", sa.UUID(), nullable=False),
        sa.Column(
            "type", sa.String(length=2), server_default=sa.text("'FS'"), nullable=False
        ),
        sa.Column(
            "lag",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
            comment="Lag in minutes (negative for lead)",
        ),
        sa.Column(
            "lag_format",
            sa.String(length=10),
            server_default=sa.text("'DURATION'"),
            nullable=False,
        ),
        sa.Column(
            "is_disabled", sa.Boolean(), server_default=sa.text("FALSE"), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "lag_format IN ('DURATION', 'PERCENT')", name="check_dependency_lag_format"
        ),
        sa.CheckConstraint(
            "type IN ('FS', 'FF', 'SS', 'SF')", name="check_dependency_type"
        ),
        sa.CheckConstraint(
            "predecessor_id != successor_id", name="check_dependency_no_self_reference"
        ),
        sa.ForeignKeyConstraint(["predecessor_id"], ["task.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["successor_id"], ["task.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "predecessor_id", "successor_id", name="uq_dependency_predecessor_successor"
        ),
    )
    op.create_index(
        "idx_dependency_predecessor", "dependency", ["predecessor_id"], unique=False
    )
    op.create_index(
        "idx_dependency_project", "dependency", ["project_id"], unique=False
    )
    op.create_index(
        "idx_dependency_successor", "dependency", ["successor_id"], unique=False
    )

    op.create_table(
        "notification",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column(
            "type",
            sa.String(length=50),
            nullable=False,
            comment="Notification type (task_assigned, mentioned, etc.)",
        ),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column(
            "entity_type",
            sa.String(length=50),
            nullable=True,
            comment="Related entity type",
        ),
        sa.Column("entity_id", sa.UUID(), nullable=True, comment="Related entity ID"),
        sa.Column("actor_id", sa.UUID(), nullable=True),
        sa.Column(
            "is_read", sa.Boolean(), server_default=sa.text("FALSE"), nullable=False
        ),
        sa.Column("read_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "email_sent", sa.Boolean(), server_default=sa.text("FALSE"), nullable=False
        ),
        sa.Column("email_sent_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["actor_id"],
            ["user.id"],
        ),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_notification_user",
        "notification",
        ["user_id", sa.literal_column("created_at DESC")],
        unique=False,
    )
    op.create_index(
        "idx_notification_user_unread",
        "notification",
        ["user_id", sa.literal_column("created_at DESC")],
        unique=False,
        postgresql_where=sa.text("NOT is_read"),
    )

    op.create_table(
        "password_reset",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column(
            "token_hash",
            sa.String(length=255),
            nullable=False,
            comment="SHA-256 hash of reset token",
        ),
        sa.Column(
            "expires_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            comment="Expiration (1 hour)",
        ),
        sa.Column(
            "used_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
            comment="When token was used",
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index(
        "idx_password_reset_user", "password_reset", ["user_id"], unique=False
    )
    op.create_index(
        op.f("ix_password_reset_user_id"), "password_reset", ["user_id"], unique=False
    )

    op.create_table(
        "project_invitation",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column(
            "invited_by_id",
            sa.UUID(),
            nullable=False,
            comment="User who sent the invitation",
        ),
        sa.Column(
            "role_id", sa.UUID(), nullable=False, comment="Role to assign when accepted"
        ),
        sa.Column(
            "email",
            sa.String(length=255),
            nullable=False,
            comment="Invitee email address",
        ),
        sa.Column(
            "token_hash",
            sa.String(length=255),
            nullable=False,
            comment="SHA-256 hash of invitation token",
        ),
        sa.Column(
            "message", sa.Text(), nullable=True, comment="Personal message from inviter"
        ),
        sa.Column(
            "expires_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            comment="Expires 7 days from creation",
        ),
        sa.Column(
            "accepted_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
            comment="When invitation was accepted",
        ),
        sa.Column(
            "is_revoked",
            sa.Boolean(),
            server_default=sa.text("FALSE"),
            nullable=False,
            comment="Invitation cancelled flag",
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["invited_by_id"], ["user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["role.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index(
        "idx_invitation_email_pending",
        "project_invitation",
        ["email"],
        unique=False,
        postgresql_where=sa.text("NOT is_revoked AND accepted_at IS NULL"),
    )
    op.create_index(
        "idx_invitation_project_pending",
        "project_invitation",
        ["project_id"],
        unique=False,
        postgresql_where=sa.text("NOT is_revoked AND accepted_at IS NULL"),
    )
    op.create_index(
        op.f("ix_project_invitation_email"),
        "project_invitation",
        ["email"],
        unique=False,
    )
    op.create_index(
        op.f("ix_project_invitation_project_id"),
        "project_invitation",
        ["project_id"],
        unique=False,
    )

    op.create_table(
        "refresh_token",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column(
            "token_hash",
            sa.String(length=255),
            nullable=False,
            comment="SHA-256 hash of refresh token",
        ),
        sa.Column(
            "device_info",
            sa.String(length=500),
            nullable=True,
            comment="User-Agent string",
        ),
        sa.Column(
            "ip_address", postgresql.INET(), nullable=True, comment="Client IP address"
        ),
        sa.Column(
            "expires_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            comment="Token expiration",
        ),
        sa.Column(
            "is_revoked", sa.Boolean(), server_default=sa.text("FALSE"), nullable=False
        ),
        sa.Column("revoked_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "revoked_reason",
            sa.String(length=100),
            nullable=True,
            comment="logout, password_change, etc.",
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index(
        "idx_refresh_token_expires",
        "refresh_token",
        ["expires_at"],
        unique=False,
        postgresql_where=sa.text("NOT is_revoked"),
    )
    op.create_index(
        "idx_refresh_token_user",
        "refresh_token",
        ["user_id"],
        unique=False,
        postgresql_where=sa.text("NOT is_revoked"),
    )
    op.create_index(
        op.f("ix_refresh_token_user_id"), "refresh_token", ["user_id"], unique=False
    )

    op.create_table(
        "resource",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("initials", sa.String(length=10), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column(
            "type",
            sa.String(length=10),
            server_default=sa.text("'WORK'"),
            nullable=False,
        ),
        sa.Column("material_label", sa.String(length=50), nullable=True),
        sa.Column(
            "max_units",
            sa.DECIMAL(precision=5, scale=2),
            server_default=sa.text("1.0"),
            nullable=False,
        ),
        sa.Column("calendar_id", sa.UUID(), nullable=True),
        sa.Column("group_name", sa.String(length=100), nullable=True),
        sa.Column("code", sa.String(length=50), nullable=True),
        sa.Column(
            "is_generic", sa.Boolean(), server_default=sa.text("FALSE"), nullable=False
        ),
        sa.Column(
            "is_active", sa.Boolean(), server_default=sa.text("TRUE"), nullable=False
        ),
        sa.Column(
            "standard_rate",
            sa.DECIMAL(precision=15, scale=4),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "overtime_rate",
            sa.DECIMAL(precision=15, scale=4),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "cost_per_use",
            sa.DECIMAL(precision=15, scale=2),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "accrue_at",
            sa.String(length=10),
            server_default=sa.text("'PRORATED'"),
            nullable=False,
        ),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("external_id", sa.String(length=100), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "accrue_at IN ('START', 'END', 'PRORATED')", name="check_resource_accrue_at"
        ),
        sa.CheckConstraint(
            "type IN ('WORK', 'MATERIAL', 'COST')", name="check_resource_type"
        ),
        sa.ForeignKeyConstraint(
            ["calendar_id"],
            ["calendar.id"],
        ),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_resource_project",
        "resource",
        ["project_id"],
        unique=False,
        postgresql_where=sa.text("is_active"),
    )
    op.create_index(
        "idx_resource_user",
        "resource",
        ["user_id"],
        unique=False,
        postgresql_where=sa.text("user_id IS NOT NULL"),
    )

    op.create_table(
        "task_baseline",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("task_id", sa.UUID(), nullable=False),
        sa.Column(
            "baseline_number",
            sa.Integer(),
            nullable=False,
            comment="Baseline number (0-10)",
        ),
        sa.Column(
            "duration",
            sa.Integer(),
            nullable=False,
            comment="Snapshot duration in minutes",
        ),
        sa.Column(
            "work", sa.Integer(), nullable=False, comment="Snapshot work in minutes"
        ),
        sa.Column(
            "start_date", sa.Date(), nullable=False, comment="Snapshot start date"
        ),
        sa.Column(
            "finish_date", sa.Date(), nullable=False, comment="Snapshot finish date"
        ),
        sa.Column(
            "cost",
            sa.DECIMAL(precision=15, scale=2),
            nullable=False,
            comment="Snapshot cost",
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Baseline save timestamp",
        ),
        sa.CheckConstraint(
            "baseline_number >= 0 AND baseline_number <= 10",
            name="check_task_baseline_number",
        ),
        sa.ForeignKeyConstraint(["task_id"], ["task.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "task_id", "baseline_number", name="uq_task_baseline_task_number"
        ),
    )
    op.create_index(
        "idx_task_baseline_task", "task_baseline", ["task_id"], unique=False
    )
    op.create_index(
        op.f("ix_task_baseline_task_id"), "task_baseline", ["task_id"], unique=False
    )

    # === Tier 5: Depends on ai_conversation, resource, task ===
    op.create_table(
        "ai_message",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("conversation_id", sa.UUID(), nullable=False),
        sa.Column(
            "role",
            sa.String(length=20),
            nullable=False,
            comment="user, assistant, system",
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "model",
            sa.String(length=100),
            nullable=True,
            comment="Model used (for assistant)",
        ),
        sa.Column("tokens_in", sa.Integer(), nullable=True, comment="Input tokens"),
        sa.Column("tokens_out", sa.Integer(), nullable=True, comment="Output tokens"),
        sa.Column(
            "latency_ms",
            sa.Integer(),
            nullable=True,
            comment="Response time in milliseconds",
        ),
        sa.Column(
            "finish_reason", sa.String(length=50), nullable=True, comment="Stop reason"
        ),
        sa.Column(
            "tool_calls",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="Tool/function calls",
        ),
        sa.Column(
            "tool_results",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="Tool results",
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "role IN ('user', 'assistant', 'system')", name="check_ai_message_role"
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"], ["ai_conversation.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_ai_message_conversation",
        "ai_message",
        ["conversation_id", "created_at"],
        unique=False,
    )

    op.create_table(
        "assignment",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("task_id", sa.UUID(), nullable=False),
        sa.Column("resource_id", sa.UUID(), nullable=False),
        sa.Column(
            "units",
            sa.DECIMAL(precision=5, scale=2),
            server_default=sa.text("1.0"),
            nullable=False,
        ),
        sa.Column("work", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "actual_work", sa.Integer(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column(
            "remaining_work", sa.Integer(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("finish_date", sa.Date(), nullable=False),
        sa.Column("actual_start", sa.Date(), nullable=True),
        sa.Column("actual_finish", sa.Date(), nullable=True),
        sa.Column(
            "work_contour",
            sa.String(length=20),
            server_default=sa.text("'FLAT'"),
            nullable=False,
        ),
        sa.Column(
            "contour_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "cost",
            sa.DECIMAL(precision=15, scale=2),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "actual_cost",
            sa.DECIMAL(precision=15, scale=2),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "remaining_cost",
            sa.DECIMAL(precision=15, scale=2),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "rate_table",
            sa.String(length=1),
            server_default=sa.text("'A'"),
            nullable=False,
        ),
        sa.Column(
            "percent_work_complete",
            sa.DECIMAL(precision=5, scale=2),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "is_confirmed",
            sa.Boolean(),
            server_default=sa.text("FALSE"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "work_contour IN ('FLAT', 'BACK_LOADED', 'FRONT_LOADED', 'DOUBLE_PEAK', 'EARLY_PEAK', 'LATE_PEAK', 'BELL', 'TURTLE', 'CONTOURED')",
            name="check_assignment_work_contour",
        ),
        sa.ForeignKeyConstraint(["resource_id"], ["resource.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["task_id"], ["task.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "task_id", "resource_id", name="uq_assignment_task_resource"
        ),
    )
    op.create_index(
        "idx_assignment_resource", "assignment", ["resource_id"], unique=False
    )
    op.create_index("idx_assignment_task", "assignment", ["task_id"], unique=False)

    op.create_table(
        "project_member",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column(
            "role_id",
            sa.UUID(),
            nullable=False,
            comment="Project role: owner, manager, member, viewer",
        ),
        sa.Column(
            "resource_id",
            sa.UUID(),
            nullable=True,
            comment="Linked resource if user is also a resource",
        ),
        sa.Column(
            "joined_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["resource_id"], ["resource.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["role_id"], ["role.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "user_id", name="uq_project_member_user"),
    )
    op.create_index(
        "idx_project_member_project", "project_member", ["project_id"], unique=False
    )
    op.create_index(
        "idx_project_member_user", "project_member", ["user_id"], unique=False
    )
    op.create_index(
        op.f("ix_project_member_project_id"),
        "project_member",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_project_member_user_id"), "project_member", ["user_id"], unique=False
    )

    op.create_table(
        "resource_availability",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("resource_id", sa.UUID(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False, comment="Period start date"),
        sa.Column(
            "end_date",
            sa.Date(),
            nullable=True,
            comment="Period end date (NULL = indefinite)",
        ),
        sa.Column(
            "units",
            sa.DECIMAL(precision=5, scale=2),
            nullable=False,
            comment="Availability (1.0 = 100%)",
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["resource_id"], ["resource.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_resource_availability",
        "resource_availability",
        ["resource_id", "start_date"],
        unique=False,
    )
    op.create_index(
        op.f("ix_resource_availability_resource_id"),
        "resource_availability",
        ["resource_id"],
        unique=False,
    )

    op.create_table(
        "resource_rate",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("resource_id", sa.UUID(), nullable=False),
        sa.Column(
            "rate_table",
            sa.Enum("A", "B", "C", "D", "E", name="ratetable"),
            server_default=sa.text("'A'"),
            nullable=False,
            comment="Rate table (A, B, C, D, E)",
        ),
        sa.Column(
            "effective_date", sa.Date(), nullable=False, comment="Effective from date"
        ),
        sa.Column(
            "standard_rate",
            sa.DECIMAL(precision=15, scale=4),
            nullable=False,
            comment="Hourly rate",
        ),
        sa.Column(
            "overtime_rate",
            sa.DECIMAL(precision=15, scale=4),
            server_default=sa.text("0"),
            nullable=False,
            comment="Overtime hourly rate",
        ),
        sa.Column(
            "cost_per_use",
            sa.DECIMAL(precision=15, scale=2),
            server_default=sa.text("0"),
            nullable=False,
            comment="Per-use cost",
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "rate_table IN ('A', 'B', 'C', 'D', 'E')", name="check_resource_rate_table"
        ),
        sa.ForeignKeyConstraint(["resource_id"], ["resource.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "resource_id",
            "rate_table",
            "effective_date",
            name="uq_resource_rate_table_date",
        ),
    )
    op.create_index(
        "idx_resource_rate_resource", "resource_rate", ["resource_id"], unique=False
    )
    op.create_index(
        op.f("ix_resource_rate_resource_id"),
        "resource_rate",
        ["resource_id"],
        unique=False,
    )

    # === Tier 6: Depends on assignment ===
    op.create_table(
        "assignment_baseline",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("assignment_id", sa.UUID(), nullable=False),
        sa.Column(
            "baseline_number",
            sa.Integer(),
            nullable=False,
            comment="Baseline number (0-10)",
        ),
        sa.Column(
            "work", sa.Integer(), nullable=False, comment="Snapshot work in minutes"
        ),
        sa.Column(
            "start_date", sa.Date(), nullable=False, comment="Snapshot start date"
        ),
        sa.Column(
            "finish_date", sa.Date(), nullable=False, comment="Snapshot finish date"
        ),
        sa.Column(
            "cost",
            sa.DECIMAL(precision=15, scale=2),
            nullable=False,
            comment="Snapshot cost",
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Baseline save timestamp",
        ),
        sa.CheckConstraint(
            "baseline_number >= 0 AND baseline_number <= 10",
            name="check_assignment_baseline_number",
        ),
        sa.ForeignKeyConstraint(
            ["assignment_id"], ["assignment.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "assignment_id", "baseline_number", name="uq_assignment_baseline_number"
        ),
    )
    op.create_index(
        "idx_assignment_baseline",
        "assignment_baseline",
        ["assignment_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_assignment_baseline_assignment_id"),
        "assignment_baseline",
        ["assignment_id"],
        unique=False,
    )

    op.create_table(
        "time_entry",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False, comment="Who logged time"),
        sa.Column("task_id", sa.UUID(), nullable=False, comment="Task worked on"),
        sa.Column(
            "assignment_id", sa.UUID(), nullable=True, comment="Related assignment"
        ),
        sa.Column("work_date", sa.Date(), nullable=False, comment="Date worked"),
        sa.Column(
            "regular_work",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
            comment="Regular work in minutes",
        ),
        sa.Column(
            "overtime_work",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
            comment="Overtime work in minutes",
        ),
        sa.Column("notes", sa.Text(), nullable=True, comment="Description of work"),
        sa.Column(
            "is_billable", sa.Boolean(), server_default=sa.text("TRUE"), nullable=False
        ),
        sa.Column(
            "billing_status",
            sa.String(length=20),
            server_default=sa.text("'UNBILLED'"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default=sa.text("'SUBMITTED'"),
            nullable=False,
        ),
        sa.Column("approved_by_id", sa.UUID(), nullable=True, comment="Approver"),
        sa.Column("approved_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "billing_status IN ('UNBILLED', 'BILLED', 'NON_BILLABLE')",
            name="check_time_entry_billing_status",
        ),
        sa.CheckConstraint(
            "status IN ('DRAFT', 'SUBMITTED', 'APPROVED', 'REJECTED')",
            name="check_time_entry_status",
        ),
        sa.ForeignKeyConstraint(
            ["approved_by_id"],
            ["user.id"],
        ),
        sa.ForeignKeyConstraint(
            ["assignment_id"], ["assignment.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["task_id"], ["task.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_time_entry_assignment",
        "time_entry",
        ["assignment_id"],
        unique=False,
        postgresql_where=sa.text("assignment_id IS NOT NULL"),
    )
    op.create_index(
        "idx_time_entry_status",
        "time_entry",
        ["status"],
        unique=False,
        postgresql_where=sa.text("status = 'SUBMITTED'"),
    )
    op.create_index("idx_time_entry_task", "time_entry", ["task_id"], unique=False)
    op.create_index(
        "idx_time_entry_user_date", "time_entry", ["user_id", "work_date"], unique=False
    )
    op.create_index(
        op.f("ix_time_entry_assignment_id"),
        "time_entry",
        ["assignment_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_time_entry_task_id"), "time_entry", ["task_id"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop in reverse order of creation
    op.drop_index(op.f("ix_time_entry_task_id"), table_name="time_entry")
    op.drop_index(op.f("ix_time_entry_assignment_id"), table_name="time_entry")
    op.drop_index("idx_time_entry_user_date", table_name="time_entry")
    op.drop_index("idx_time_entry_task", table_name="time_entry")
    op.drop_index(
        "idx_time_entry_status",
        table_name="time_entry",
        postgresql_where=sa.text("status = 'SUBMITTED'"),
    )
    op.drop_index(
        "idx_time_entry_assignment",
        table_name="time_entry",
        postgresql_where=sa.text("assignment_id IS NOT NULL"),
    )
    op.drop_table("time_entry")
    op.drop_index(
        op.f("ix_assignment_baseline_assignment_id"), table_name="assignment_baseline"
    )
    op.drop_index("idx_assignment_baseline", table_name="assignment_baseline")
    op.drop_table("assignment_baseline")
    op.drop_index(op.f("ix_resource_rate_resource_id"), table_name="resource_rate")
    op.drop_index("idx_resource_rate_resource", table_name="resource_rate")
    op.drop_table("resource_rate")
    op.drop_index(
        op.f("ix_resource_availability_resource_id"), table_name="resource_availability"
    )
    op.drop_index("idx_resource_availability", table_name="resource_availability")
    op.drop_table("resource_availability")
    op.drop_index(op.f("ix_project_member_user_id"), table_name="project_member")
    op.drop_index(op.f("ix_project_member_project_id"), table_name="project_member")
    op.drop_index("idx_project_member_user", table_name="project_member")
    op.drop_index("idx_project_member_project", table_name="project_member")
    op.drop_table("project_member")
    op.drop_index("idx_assignment_task", table_name="assignment")
    op.drop_index("idx_assignment_resource", table_name="assignment")
    op.drop_table("assignment")
    op.drop_index("idx_ai_message_conversation", table_name="ai_message")
    op.drop_table("ai_message")
    op.drop_index(op.f("ix_task_baseline_task_id"), table_name="task_baseline")
    op.drop_index("idx_task_baseline_task", table_name="task_baseline")
    op.drop_table("task_baseline")
    op.drop_index(
        "idx_resource_user",
        table_name="resource",
        postgresql_where=sa.text("user_id IS NOT NULL"),
    )
    op.drop_index(
        "idx_resource_project",
        table_name="resource",
        postgresql_where=sa.text("is_active"),
    )
    op.drop_table("resource")
    op.drop_index(op.f("ix_refresh_token_user_id"), table_name="refresh_token")
    op.drop_index(
        "idx_refresh_token_user",
        table_name="refresh_token",
        postgresql_where=sa.text("NOT is_revoked"),
    )
    op.drop_index(
        "idx_refresh_token_expires",
        table_name="refresh_token",
        postgresql_where=sa.text("NOT is_revoked"),
    )
    op.drop_table("refresh_token")
    op.drop_index(
        op.f("ix_project_invitation_project_id"), table_name="project_invitation"
    )
    op.drop_index(op.f("ix_project_invitation_email"), table_name="project_invitation")
    op.drop_index(
        "idx_invitation_project_pending",
        table_name="project_invitation",
        postgresql_where=sa.text("NOT is_revoked AND accepted_at IS NULL"),
    )
    op.drop_index(
        "idx_invitation_email_pending",
        table_name="project_invitation",
        postgresql_where=sa.text("NOT is_revoked AND accepted_at IS NULL"),
    )
    op.drop_table("project_invitation")
    op.drop_index(op.f("ix_password_reset_user_id"), table_name="password_reset")
    op.drop_index("idx_password_reset_user", table_name="password_reset")
    op.drop_table("password_reset")
    op.drop_index(
        "idx_notification_user_unread",
        table_name="notification",
        postgresql_where=sa.text("NOT is_read"),
    )
    op.drop_index("idx_notification_user", table_name="notification")
    op.drop_table("notification")
    op.drop_index("idx_dependency_successor", table_name="dependency")
    op.drop_index("idx_dependency_project", table_name="dependency")
    op.drop_index("idx_dependency_predecessor", table_name="dependency")
    op.drop_table("dependency")
    op.drop_index(op.f("ix_comment_parent_comment_id"), table_name="comment")
    op.drop_index(op.f("ix_comment_author_id"), table_name="comment")
    op.drop_index(
        "idx_comment_parent",
        table_name="comment",
        postgresql_where=sa.text("parent_comment_id IS NOT NULL"),
    )
    op.drop_index(
        "idx_comment_entity",
        table_name="comment",
        postgresql_where=sa.text("NOT is_deleted"),
    )
    op.drop_index(
        "idx_comment_author",
        table_name="comment",
        postgresql_where=sa.text("NOT is_deleted"),
    )
    op.drop_table("comment")
    op.drop_index(
        "idx_attachment_entity",
        table_name="attachment",
        postgresql_where=sa.text("NOT is_deleted"),
    )
    op.drop_table("attachment")
    op.drop_index("idx_ai_usage_user_date", table_name="ai_usage")
    op.drop_index("idx_ai_usage_date", table_name="ai_usage")
    op.drop_table("ai_usage")
    op.drop_index(op.f("ix_ai_conversation_user_id"), table_name="ai_conversation")
    op.drop_index(op.f("ix_ai_conversation_project_id"), table_name="ai_conversation")
    op.drop_index("idx_ai_conversation_user", table_name="ai_conversation")
    op.drop_index("idx_ai_conversation_project", table_name="ai_conversation")
    op.drop_table("ai_conversation")
    op.drop_index("idx_activity_log_user", table_name="activity_log")
    op.drop_index(
        "idx_activity_log_project",
        table_name="activity_log",
        postgresql_where=sa.text("project_id IS NOT NULL"),
    )
    op.drop_index("idx_activity_log_entity", table_name="activity_log")
    op.drop_table("activity_log")
    op.drop_index(op.f("ix_task_project_id"), table_name="task")
    op.drop_index(
        "idx_task_project_wbs",
        table_name="task",
        postgresql_where=sa.text("NOT is_deleted"),
    )
    op.drop_index(
        "idx_task_project_order",
        table_name="task",
        postgresql_where=sa.text("NOT is_deleted"),
    )
    op.drop_index(
        "idx_task_project",
        table_name="task",
        postgresql_where=sa.text("NOT is_deleted"),
    )
    op.drop_index(
        "idx_task_parent", table_name="task", postgresql_where=sa.text("NOT is_deleted")
    )
    op.drop_index(
        "idx_task_dates", table_name="task", postgresql_where=sa.text("NOT is_deleted")
    )
    op.drop_table("task")
    op.drop_index(
        op.f("ix_calendar_exception_calendar_id"), table_name="calendar_exception"
    )
    op.drop_index("idx_calendar_exception_dates", table_name="calendar_exception")
    op.drop_index("idx_calendar_exception_calendar", table_name="calendar_exception")
    op.drop_table("calendar_exception")
    # Drop deferred FK before dropping project/calendar
    op.drop_constraint("fk_calendar_project_id", "calendar", type_="foreignkey")
    op.drop_index(op.f("ix_project_owner_id"), table_name="project")
    op.drop_index(
        "idx_project_status",
        table_name="project",
        postgresql_where=sa.text("NOT is_deleted"),
    )
    op.drop_index(
        "idx_project_owner",
        table_name="project",
        postgresql_where=sa.text("NOT is_deleted"),
    )
    op.drop_table("project")
    op.drop_index(op.f("ix_calendar_project_id"), table_name="calendar")
    op.drop_index("idx_calendar_project", table_name="calendar")
    op.drop_table("calendar")
    op.drop_index(op.f("ix_user_email"), table_name="user")
    op.drop_index(
        "idx_user_oauth",
        table_name="user",
        postgresql_where=sa.text("oauth_provider IS NOT NULL"),
    )
    op.drop_table("user")
    op.drop_index(op.f("ix_role_name"), table_name="role")
    op.drop_table("role")
