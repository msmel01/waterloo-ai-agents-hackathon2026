"""Domain enums for Valentine Hotline backend."""

from enum import Enum


class SessionStatus(str, Enum):
    """Interview session lifecycle status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SCORING = "scoring"
    SCORED = "scored"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ConversationSpeaker(str, Enum):
    """Speaker labels for transcript turns."""

    AVATAR = "avatar"
    SUITOR = "suitor"


class Verdict(str, Enum):
    """Final matchmaking verdict."""

    DATE = "date"
    NO_DATE = "no_date"


class BookingStatus(str, Enum):
    """Booking lifecycle status."""

    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"
