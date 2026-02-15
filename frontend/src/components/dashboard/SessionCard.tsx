import { Link } from 'react-router-dom';
import type { SessionSummary } from '../../types/dashboard';

type Props = {
  session: SessionSummary;
};

function verdictMeta(verdict: SessionSummary['verdict'], status: string) {
  if (verdict === 'date') return { icon: '💚', text: 'Date', color: 'text-green-600' };
  if (verdict === 'no_date') return { icon: '💔', text: 'No Date', color: 'text-rose-600' };
  if (status === 'failed') return { icon: '❌', text: 'Failed', color: 'text-slate-500' };
  return { icon: '⏳', text: 'Pending', color: 'text-amber-600' };
}

export function SessionCard({ session }: Props) {
  const meta = verdictMeta(session.verdict, session.status);
  const dateText = session.started_at ? new Date(session.started_at).toLocaleString() : 'No start time';
  return (
    <Link
      to={`/dashboard/sessions/${session.session_id}`}
      className="block rounded-xl border border-slate-200 bg-white p-4 shadow-sm transition hover:border-violet-300"
    >
      <div className="flex items-center justify-between gap-3">
        <div className="min-w-0">
          <p className="truncate text-base font-semibold text-slate-900">
            {meta.icon} {session.suitor_name}
          </p>
          <p className="text-xs text-slate-500">{dateText}</p>
        </div>
        <div className={`text-sm font-semibold ${meta.color}`}>
          {session.scores ? `Score ${session.scores.aggregate.toFixed(1)}` : meta.text}
        </div>
      </div>
      <p className="mt-2 text-sm text-slate-600">
        {session.questions_asked} questions
        {session.duration_seconds ? ` · ${Math.floor(session.duration_seconds / 60)}m ${session.duration_seconds % 60}s` : ''}
        {session.has_booking && session.booking_date ? ` · Booked ${new Date(session.booking_date).toLocaleString()}` : ''}
      </p>
    </Link>
  );
}
