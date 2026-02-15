import type { VerdictScores } from '../../types/results';

interface ScoreBreakdownProps {
  scores: VerdictScores;
}

function colorClass(score: number) {
  if (score >= 80) return 'bg-green-500';
  if (score >= 60) return 'bg-amber-500';
  return 'bg-rose-500';
}

export function ScoreBreakdown({ scores }: ScoreBreakdownProps) {
  const rows: Array<keyof Omit<VerdictScores, 'aggregate'>> = [
    'effort',
    'creativity',
    'intent_clarity',
    'emotional_intelligence',
  ];

  return (
    <section className="m6-card space-y-4">
      <h3 className="text-white text-lg font-semibold">Score Breakdown</h3>
      {rows.map((key, index) => {
        const item = scores[key];
        const safe = Math.max(0, Math.min(100, item.score));
        return (
          <div key={key} className="space-y-1" style={{ animationDelay: `${index * 0.2}s` }}>
            <div className="flex justify-between text-xs text-rose-50">
              <span>{item.label}</span>
              <span>
                {Math.round(item.score)}/100 ({Math.round(item.weight * 100)}%)
              </span>
            </div>
            <div className="h-2 bg-white/20 rounded">
              <div
                className={`h-2 rounded m6-grow ${colorClass(safe)}`}
                style={{ width: `${safe}%` }}
              />
            </div>
          </div>
        );
      })}
      <div className="pt-2 border-t border-white/20 flex justify-between text-white">
        <span>Overall Score</span>
        <span className="font-semibold">{scores.aggregate.toFixed(2)} / 100</span>
      </div>
    </section>
  );
}
