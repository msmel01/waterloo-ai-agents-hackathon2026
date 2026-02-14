"""full_valentine_hotline_schema

Revision ID: 9a6f3c2b1d10
Revises: 6c66fe9f5302
Create Date: 2026-02-14 09:30:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "9a6f3c2b1d10"
down_revision: Union[str, Sequence[str], None] = "6c66fe9f5302"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


session_status_enum = sa.Enum(
    "pending",
    "in_progress",
    "completed",
    "failed",
    "cancelled",
    name="session_status",
)
conversation_speaker_enum = sa.Enum("avatar", "suitor", name="conversation_speaker")
verdict_enum = sa.Enum("date", "no_date", name="verdict")
booking_status_enum = sa.Enum(
    "confirmed",
    "cancelled",
    "rescheduled",
    name="booking_status",
)


def upgrade() -> None:
    """Upgrade schema."""
    session_status_enum.create(op.get_bind(), checkfirst=True)
    conversation_speaker_enum.create(op.get_bind(), checkfirst=True)
    verdict_enum.create(op.get_bind(), checkfirst=True)
    booking_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "hearts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("clerk_user_id", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("photo_url", sa.String(length=1024), nullable=True),
        sa.Column("video_url", sa.String(length=1024), nullable=True),
        sa.Column("tavus_avatar_id", sa.String(length=255), nullable=True),
        sa.Column("persona", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "expectations", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column("calcom_user_id", sa.String(length=255), nullable=True),
        sa.Column("calcom_event_type_id", sa.String(length=255), nullable=True),
        sa.Column("shareable_slug", sa.String(length=255), nullable=False),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_hearts_clerk_user_id", "hearts", ["clerk_user_id"], unique=True)
    op.create_index("ix_hearts_email", "hearts", ["email"], unique=True)
    op.create_index(
        "ix_hearts_shareable_slug", "hearts", ["shareable_slug"], unique=True
    )
    op.create_index("ix_hearts_is_active", "hearts", ["is_active"], unique=False)

    op.create_table(
        "screening_questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("heart_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column(
            "is_required", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["heart_id"], ["hearts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_screening_questions_heart_id",
        "screening_questions",
        ["heart_id"],
        unique=False,
    )
    op.create_index(
        "ix_screening_questions_order_index",
        "screening_questions",
        ["order_index"],
        unique=False,
    )

    op.create_table(
        "suitors",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("intro_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_suitors_email", "suitors", ["email"], unique=False)

    op.create_table(
        "sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("heart_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("suitor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("livekit_room_name", sa.String(length=255), nullable=True),
        sa.Column(
            "status", session_status_enum, nullable=False, server_default="pending"
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["heart_id"], ["hearts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["suitor_id"], ["suitors.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sessions_heart_id", "sessions", ["heart_id"], unique=False)
    op.create_index("ix_sessions_suitor_id", "sessions", ["suitor_id"], unique=False)
    op.create_index("ix_sessions_status", "sessions", ["status"], unique=False)

    op.create_table(
        "conversation_turns",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("turn_index", sa.Integer(), nullable=False),
        sa.Column("speaker", conversation_speaker_enum, nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "emotion_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_conversation_turns_session_id",
        "conversation_turns",
        ["session_id"],
        unique=False,
    )
    op.create_index(
        "ix_conversation_turns_turn_index",
        "conversation_turns",
        ["turn_index"],
        unique=False,
    )
    op.create_index(
        "ix_conversation_turns_speaker", "conversation_turns", ["speaker"], unique=False
    )

    op.create_table(
        "scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("effort_score", sa.Float(), nullable=False),
        sa.Column("creativity_score", sa.Float(), nullable=False),
        sa.Column("intent_clarity_score", sa.Float(), nullable=False),
        sa.Column("emotional_intelligence_score", sa.Float(), nullable=False),
        sa.Column("weighted_total", sa.Float(), nullable=False),
        sa.Column(
            "emotion_modifiers", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column("verdict", verdict_enum, nullable=False),
        sa.Column("feedback_text", sa.Text(), nullable=False),
        sa.Column("raw_llm_response", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id"),
    )
    op.create_index("ix_scores_session_id", "scores", ["session_id"], unique=True)
    op.create_index(
        "ix_scores_weighted_total", "scores", ["weighted_total"], unique=False
    )
    op.create_index("ix_scores_verdict", "scores", ["verdict"], unique=False)

    op.create_table(
        "bookings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("heart_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("suitor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("calcom_booking_id", sa.String(length=255), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status", booking_status_enum, nullable=False, server_default="confirmed"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["heart_id"], ["hearts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["suitor_id"], ["suitors.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_bookings_session_id", "bookings", ["session_id"], unique=False)
    op.create_index("ix_bookings_heart_id", "bookings", ["heart_id"], unique=False)
    op.create_index("ix_bookings_suitor_id", "bookings", ["suitor_id"], unique=False)
    op.create_index(
        "ix_bookings_calcom_booking_id", "bookings", ["calcom_booking_id"], unique=False
    )
    op.create_index(
        "ix_bookings_scheduled_at", "bookings", ["scheduled_at"], unique=False
    )
    op.create_index("ix_bookings_status", "bookings", ["status"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_bookings_status", table_name="bookings")
    op.drop_index("ix_bookings_scheduled_at", table_name="bookings")
    op.drop_index("ix_bookings_calcom_booking_id", table_name="bookings")
    op.drop_index("ix_bookings_suitor_id", table_name="bookings")
    op.drop_index("ix_bookings_heart_id", table_name="bookings")
    op.drop_index("ix_bookings_session_id", table_name="bookings")
    op.drop_table("bookings")

    op.drop_index("ix_scores_verdict", table_name="scores")
    op.drop_index("ix_scores_weighted_total", table_name="scores")
    op.drop_index("ix_scores_session_id", table_name="scores")
    op.drop_table("scores")

    op.drop_index("ix_conversation_turns_speaker", table_name="conversation_turns")
    op.drop_index("ix_conversation_turns_turn_index", table_name="conversation_turns")
    op.drop_index("ix_conversation_turns_session_id", table_name="conversation_turns")
    op.drop_table("conversation_turns")

    op.drop_index("ix_sessions_status", table_name="sessions")
    op.drop_index("ix_sessions_suitor_id", table_name="sessions")
    op.drop_index("ix_sessions_heart_id", table_name="sessions")
    op.drop_table("sessions")

    op.drop_index("ix_suitors_email", table_name="suitors")
    op.drop_table("suitors")

    op.drop_index(
        "ix_screening_questions_order_index", table_name="screening_questions"
    )
    op.drop_index("ix_screening_questions_heart_id", table_name="screening_questions")
    op.drop_table("screening_questions")

    op.drop_index("ix_hearts_is_active", table_name="hearts")
    op.drop_index("ix_hearts_shareable_slug", table_name="hearts")
    op.drop_index("ix_hearts_email", table_name="hearts")
    op.drop_index("ix_hearts_clerk_user_id", table_name="hearts")
    op.drop_table("hearts")

    booking_status_enum.drop(op.get_bind(), checkfirst=True)
    verdict_enum.drop(op.get_bind(), checkfirst=True)
    conversation_speaker_enum.drop(op.get_bind(), checkfirst=True)
    session_status_enum.drop(op.get_bind(), checkfirst=True)
