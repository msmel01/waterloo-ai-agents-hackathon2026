import { Link } from 'react-router-dom';

import { ShareCard } from './ShareCard';

interface NoDateEncouragementProps {
  bestMetricLabel: string;
  bestMetricScore: number;
  score: number;
}

export function NoDateEncouragement({
  bestMetricLabel,
  bestMetricScore,
  score,
}: NoDateEncouragementProps) {
  return (
    <section className="m6-card m6-card-nodate space-y-4">
      <h3 className="text-xl text-white font-semibold">💜 Keep Your Head Up!</h3>
      <p className="text-sm text-rose-100">
        Not every match is meant to be, but every conversation helps you grow. The right person
        will notice what you bring.
      </p>
      <p className="text-sm text-rose-100">
        Your strongest category was <span className="font-semibold">{bestMetricLabel}</span> at{' '}
        <span className="font-semibold">{Math.round(bestMetricScore)}/100</span>. That takes courage.
      </p>
      <div className="flex flex-wrap gap-3">
        <ShareCard verdict="no_date" score={score} />
        <Link
          to="/chats"
          className="px-4 py-2 rounded border border-white/30 text-white text-sm hover:bg-white/10"
        >
          🏠 Try Again?
        </Link>
      </div>
    </section>
  );
}
