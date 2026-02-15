export type VerdictStatus = 'scoring' | 'scored';
export type VerdictValue = 'date' | 'no_date';

export interface ScoreMetric {
  score: number;
  weight: number;
  label: string;
}

export interface VerdictScores {
  effort: ScoreMetric;
  creativity: ScoreMetric;
  intent_clarity: ScoreMetric;
  emotional_intelligence: ScoreMetric;
  aggregate: number;
}

export interface VerdictFeedback {
  summary: string;
  strengths: string[];
  improvements: string[];
  favorite_moment: string;
}

export interface VerdictResponse {
  session_id: string;
  status: VerdictStatus;
  ready?: boolean;
  verdict?: VerdictValue;
  scores?: VerdictScores;
  feedback?: VerdictFeedback;
  booking_available?: boolean;
  suitor_name?: string;
  heart_name?: string;
  message?: string;
}

export interface SlotTime {
  start: string;
  end: string;
  display: string;
}

export interface SlotDay {
  date: string;
  day_label: string;
  times: SlotTime[];
}

export interface SlotsResponse {
  slots: SlotDay[];
  timezone: string;
  event_duration_minutes: number;
}

export interface BookingRequest {
  slot_start: string;
  suitor_name: string;
  suitor_email: string;
  suitor_notes?: string;
}

export interface BookingResponse {
  booking_id: string;
  cal_event_id: string;
  slot: {
    start: string;
    end: string;
    display: string;
  };
  status: string;
  message: string;
}
