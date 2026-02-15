export interface DashboardStats {
  total_suitors: number;
  total_sessions: number;
  completed_sessions: number;
  active_sessions: number;
  failed_sessions: number;
  total_dates: number;
  total_rejections: number;
  match_rate: number;
  avg_scores: {
    effort: number;
    creativity: number;
    intent_clarity: number;
    emotional_intelligence: number;
    aggregate: number;
  };
  score_distribution: {
    excellent: number;
    good: number;
    average: number;
    below_average: number;
  };
  recent_activity: {
    sessions_today: number;
    sessions_this_week: number;
    sessions_this_month: number;
  };
  bookings: {
    total_booked: number;
    upcoming: number;
    booking_rate: number;
  };
}

export interface SessionSummary {
  session_id: string;
  suitor_name: string;
  suitor_intro: string | null;
  started_at: string | null;
  ended_at: string | null;
  duration_seconds: number | null;
  status: string;
  questions_asked: number;
  scores: {
    effort: number;
    creativity: number;
    intent_clarity: number;
    emotional_intelligence: number;
    aggregate: number;
  } | null;
  verdict: 'date' | 'no_date' | 'pending';
  has_booking: boolean;
  booking_date: string | null;
}

export interface SessionListResponse {
  sessions: SessionSummary[];
  pagination: {
    page: number;
    per_page: number;
    total: number;
    total_pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
}

export interface SessionDetail {
  session_id: string;
  suitor: {
    id: string;
    name: string;
    intro_message: string | null;
    created_at: string;
  };
  session: {
    status: string;
    started_at: string | null;
    ended_at: string | null;
    duration_seconds: number | null;
    livekit_room_name: string | null;
  };
  transcript: {
    turn: number;
    question: string;
    answer: string;
    timestamp: string;
  }[];
  scores: {
    effort: { score: number; weight: number; label: string };
    creativity: { score: number; weight: number; label: string };
    intent_clarity: { score: number; weight: number; label: string };
    emotional_intelligence: { score: number; weight: number; label: string };
    aggregate: number;
  } | null;
  verdict: 'date' | 'no_date' | null;
  feedback: {
    summary: string;
    strengths: string[];
    improvements: string[];
    favorite_moment: string;
  } | null;
  booking: {
    booking_id: string;
    cal_event_id: string;
    booked_at: string;
    slot_start: string;
    suitor_email: string | null;
    suitor_notes: string | null;
    status: string;
  } | null;
}

export interface TrendData {
  period: 'daily' | 'weekly';
  data: {
    date: string;
    sessions: number;
    avg_aggregate: number;
    dates: number;
    rejections: number;
  }[];
}

export interface HeartStatus {
  slug: string;
  name: string;
  active: boolean;
  total_sessions: number;
  link: string;
  deactivated_at?: string | null;
  message?: string | null;
}

export interface SessionQueryParams {
  page?: number;
  per_page?: number;
  verdict?: string;
  sort_by?: string;
  sort_order?: string;
  search?: string;
  date_from?: string;
  date_to?: string;
}
