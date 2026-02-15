import { useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import { AppHeader } from '../../components/AppHeader';
import { BookingConfirmation } from '../../components/results/BookingConfirmation';
import { FeedbackDisplay } from '../../components/results/FeedbackDisplay';
import { NoDateEncouragement } from '../../components/results/NoDateEncouragement';
import { ScoreBreakdown } from '../../components/results/ScoreBreakdown';
import { SlotPicker } from '../../components/results/SlotPicker';
import { VerdictReveal } from '../../components/results/VerdictReveal';
import { WaitingScreen } from '../../components/results/WaitingScreen';
import { useVerdictPolling } from '../../hooks/useVerdictPolling';
import type { BookingResponse } from '../../types/results';

export function ResultsPage() {
  const { sessionId = '' } = useParams<{ sessionId: string }>();
  const verdictQuery = useVerdictPolling(sessionId);
  const [booking, setBooking] = useState<BookingResponse | null>(null);
  const [bookingEmail, setBookingEmail] = useState('');

  const verdict = verdictQuery.data;

  const bestMetric = useMemo(() => {
    const scores = verdict?.scores;
    if (!scores) {
      return null;
    }
    const entries = [
      scores.effort,
      scores.creativity,
      scores.intent_clarity,
      scores.emotional_intelligence,
    ];
    return entries.sort((a, b) => b.score - a.score)[0];
  }, [verdict?.scores]);

  return (
    <div className="min-h-screen m6-results-bg py-6 px-4">
      <div className="max-w-3xl mx-auto space-y-4">
        <AppHeader />

        {verdictQuery.isLoading || verdict?.status === 'scoring' ? <WaitingScreen /> : null}

        {!verdictQuery.isLoading && verdict?.status === 'scored' && verdict.verdict ? (
          <>
            <VerdictReveal verdict={verdict.verdict} />
            {verdict.scores ? <ScoreBreakdown scores={verdict.scores} /> : null}
            {verdict.feedback ? <FeedbackDisplay feedback={verdict.feedback} /> : null}

            {booking ? (
              <BookingConfirmation
                booking={booking}
                email={bookingEmail}
                score={verdict.scores?.aggregate ?? 0}
              />
            ) : verdict.verdict === 'date' && verdict.booking_available ? (
              <SlotPicker
                sessionId={sessionId}
                enabled
                suitorName={verdict.suitor_name || 'Suitor'}
                onBooked={(value, email) => {
                  setBooking(value);
                  setBookingEmail(email);
                }}
              />
            ) : verdict.verdict === 'no_date' ? (
              <NoDateEncouragement
                bestMetricLabel={bestMetric?.label || 'Effort'}
                bestMetricScore={bestMetric?.score ?? 0}
                score={verdict.scores?.aggregate ?? 0}
              />
            ) : null}
          </>
        ) : null}

        {verdictQuery.isError ? (
          <section className="m6-card space-y-3 text-center">
            <p className="text-rose-100 text-sm">Could not load your results right now.</p>
            <button
              type="button"
              className="px-4 py-2 rounded border border-white/30 text-white text-sm"
              onClick={() => verdictQuery.refetch()}
            >
              Retry
            </button>
            <Link to="/chats" className="block text-rose-200 text-sm underline">
              Back to chats
            </Link>
          </section>
        ) : null}
      </div>
    </div>
  );
}
