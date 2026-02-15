"""Schemas for simplified M7 dashboard APIs."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class DashboardAvgScores(BaseModel):
    effort: float
    creativity: float
    intent_clarity: float
    emotional_intelligence: float
    aggregate: float


class DashboardScoreDistribution(BaseModel):
    excellent: int
    good: int
    average: int
    below_average: int


class DashboardRecentActivity(BaseModel):
    sessions_today: int
    sessions_this_week: int
    sessions_this_month: int


class DashboardBookingsStats(BaseModel):
    total_booked: int
    upcoming: int
    booking_rate: float


class DashboardStatsResponse(BaseModel):
    total_suitors: int
    total_sessions: int
    completed_sessions: int
    active_sessions: int
    failed_sessions: int
    total_dates: int
    total_rejections: int
    match_rate: float
    avg_scores: DashboardAvgScores
    score_distribution: DashboardScoreDistribution
    recent_activity: DashboardRecentActivity
    bookings: DashboardBookingsStats


class DashboardSessionScores(BaseModel):
    effort: float
    creativity: float
    intent_clarity: float
    emotional_intelligence: float
    aggregate: float


class DashboardSessionSummary(BaseModel):
    session_id: str
    suitor_name: str
    suitor_intro: str | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    duration_seconds: int | None = None
    status: str
    questions_asked: int
    scores: DashboardSessionScores | None = None
    verdict: Literal["date", "no_date", "pending"] = "pending"
    has_booking: bool
    booking_date: datetime | None = None


class DashboardPagination(BaseModel):
    page: int
    per_page: int
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool


class DashboardSessionsResponse(BaseModel):
    sessions: list[DashboardSessionSummary]
    pagination: DashboardPagination


class DashboardSuitorBlock(BaseModel):
    id: str
    name: str
    intro_message: str | None = None
    created_at: datetime


class DashboardSessionBlock(BaseModel):
    status: str
    started_at: datetime | None = None
    ended_at: datetime | None = None
    duration_seconds: int | None = None
    livekit_room_name: str | None = None


class DashboardTranscriptTurn(BaseModel):
    turn: int
    question: str
    answer: str
    timestamp: datetime | str


class DashboardWeightedScore(BaseModel):
    score: float
    weight: float
    label: str


class DashboardScoresBlock(BaseModel):
    effort: DashboardWeightedScore
    creativity: DashboardWeightedScore
    intent_clarity: DashboardWeightedScore
    emotional_intelligence: DashboardWeightedScore
    aggregate: float


class DashboardFeedbackBlock(BaseModel):
    summary: str
    strengths: list[str]
    improvements: list[str]
    favorite_moment: str


class DashboardBookingBlock(BaseModel):
    booking_id: str
    cal_event_id: str
    booked_at: datetime
    slot_start: datetime
    suitor_email: str | None = None
    suitor_notes: str | None = None
    status: str


class DashboardSessionDetailResponse(BaseModel):
    session_id: str
    suitor: DashboardSuitorBlock
    session: DashboardSessionBlock
    transcript: list[DashboardTranscriptTurn]
    scores: DashboardScoresBlock | None = None
    verdict: Literal["date", "no_date"] | None = None
    feedback: DashboardFeedbackBlock | None = None
    booking: DashboardBookingBlock | None = None


class DashboardHeartStatusResponse(BaseModel):
    slug: str
    name: str
    active: bool
    total_sessions: int
    link: str
    deactivated_at: datetime | None = None
    message: str | None = None


class DashboardHeartStatusPatchRequest(BaseModel):
    active: bool = Field(description="Whether screening link is active")


class DashboardTrendPoint(BaseModel):
    date: str
    sessions: int
    avg_aggregate: float
    dates: int
    rejections: int


class DashboardTrendsResponse(BaseModel):
    period: Literal["daily", "weekly"]
    data: list[DashboardTrendPoint]
