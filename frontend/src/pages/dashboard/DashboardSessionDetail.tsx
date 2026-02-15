import { Link, useParams } from 'react-router-dom';
import { DashboardLayout } from '../../components/dashboard/DashboardLayout';
import { TranscriptView } from '../../components/dashboard/TranscriptView';
import { useSessionDetail } from '../../hooks/useSessionDetail';
import { useHeartStatus } from '../../hooks/useHeartStatus';

function badge(verdict: 'date' | 'no_date' | null) {
  if (verdict === 'date') return 'bg-green-100 text-green-700';
  if (verdict === 'no_date') return 'bg-rose-100 text-rose-700';
  return 'bg-amber-100 text-amber-700';
}

export function DashboardSessionDetail() {
  const { id } = useParams();
  const detailQuery = useSessionDetail(id);
  const { statusQuery, toggleMutation } = useHeartStatus();
  const data = detailQuery.data;

  return (
    <DashboardLayout
      active={statusQuery.data?.active}
      loadingStatus={toggleMutation.isPending}
      onToggleStatus={(active) => toggleMutation.mutate(active)}
    >
      <Link to="/dashboard/sessions" className="text-sm font-medium text-violet-600">
        ← Back to Sessions
      </Link>

      {detailQuery.isLoading ? (
        <p className="mt-4 text-sm text-slate-500">Loading session detail...</p>
      ) : !data ? (
        <p className="mt-4 text-sm text-rose-600">Session not found.</p>
      ) : (
        <div className="mt-4 space-y-4">
          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="flex items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-semibold text-slate-900">{data.suitor.name}'s Interview</h2>
                <p className="mt-1 text-sm text-slate-500">
                  {data.session.started_at ? new Date(data.session.started_at).toLocaleString() : 'Unknown start'}
                  {data.session.duration_seconds ? ` · ${Math.floor(data.session.duration_seconds / 60)}m ${data.session.duration_seconds % 60}s` : ''}
                </p>
                {data.suitor.intro_message && (
                  <p className="mt-2 text-sm text-slate-700">"{data.suitor.intro_message}"</p>
                )}
              </div>
              <span className={`rounded-full px-3 py-1 text-sm font-semibold ${badge(data.verdict)}`}>
                {data.verdict === 'date' ? 'DATE' : data.verdict === 'no_date' ? 'NO DATE' : 'PENDING'}
              </span>
            </div>
          </div>

          {data.scores ? (
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <h3 className="text-base font-semibold text-slate-900">Score Breakdown</h3>
              <div className="mt-3 space-y-3">
                {[
                  data.scores.effort,
                  data.scores.creativity,
                  data.scores.intent_clarity,
                  data.scores.emotional_intelligence,
                ].map((item) => (
                  <div key={item.label}>
                    <div className="mb-1 flex items-center justify-between text-sm">
                      <span className="text-slate-700">{item.label}</span>
                      <span className="font-semibold text-slate-900">{item.score.toFixed(1)}</span>
                    </div>
                    <div className="h-2 rounded-full bg-slate-100">
                      <div
                        className="h-2 rounded-full bg-violet-500"
                        style={{ width: `${Math.max(0, Math.min(100, item.score))}%` }}
                      />
                    </div>
                  </div>
                ))}
                <p className="pt-2 text-sm font-semibold text-slate-900">
                  Overall: {data.scores.aggregate.toFixed(1)} / 100
                </p>
              </div>
            </div>
          ) : (
            <div className="rounded-xl border border-slate-200 bg-white p-4 text-sm text-amber-700 shadow-sm">
              Scoring in progress...
            </div>
          )}

          {data.feedback && (
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <h3 className="text-base font-semibold text-slate-900">Feedback</h3>
              <p className="mt-2 text-sm text-slate-700">"{data.feedback.summary}"</p>
              <div className="mt-3 grid gap-3 md:grid-cols-2">
                <div>
                  <p className="text-sm font-semibold text-slate-800">Strengths</p>
                  <ul className="mt-1 list-disc pl-5 text-sm text-slate-700">
                    {data.feedback.strengths.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <p className="text-sm font-semibold text-slate-800">Areas to Grow</p>
                  <ul className="mt-1 list-disc pl-5 text-sm text-slate-700">
                    {data.feedback.improvements.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
              </div>
              {data.feedback.favorite_moment && (
                <p className="mt-3 rounded bg-violet-50 p-3 text-sm text-violet-800">
                  ⭐ {data.feedback.favorite_moment}
                </p>
              )}
            </div>
          )}

          <TranscriptView transcript={data.transcript} />

          {data.booking && (
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <h3 className="text-base font-semibold text-slate-900">Booking</h3>
              <p className="mt-2 text-sm text-slate-700">
                📅 {new Date(data.booking.slot_start).toLocaleString()}
              </p>
              <p className="text-sm text-slate-700">📧 {data.booking.suitor_email || '-'}</p>
              {data.booking.suitor_notes && <p className="text-sm text-slate-700">📝 {data.booking.suitor_notes}</p>}
              <p className="text-sm text-slate-700">Status: {data.booking.status}</p>
            </div>
          )}
        </div>
      )}
    </DashboardLayout>
  );
}
