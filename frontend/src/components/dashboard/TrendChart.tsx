import type { TrendData } from '../../types/dashboard';

type Props = {
  trend: TrendData | undefined;
};

export function TrendChart({ trend }: Props) {
  const points = trend?.data ?? [];
  const maxAvg = Math.max(1, ...points.map((p) => p.avg_aggregate));
  const path = points
    .map((p, i) => {
      const x = points.length <= 1 ? 0 : (i / (points.length - 1)) * 100;
      const y = 100 - (p.avg_aggregate / maxAvg) * 100;
      return `${x},${y}`;
    })
    .join(' ');

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <h3 className="text-base font-semibold text-slate-900">Score Trends</h3>
      {points.length === 0 ? (
        <p className="mt-3 text-sm text-slate-500">No trend data yet.</p>
      ) : (
        <div className="mt-3">
          <svg viewBox="0 0 100 40" className="h-32 w-full">
            <polyline fill="none" stroke="#8b5cf6" strokeWidth="2" points={path} />
          </svg>
          <div className="grid grid-cols-2 gap-2 text-xs text-slate-500 md:grid-cols-4">
            {points.slice(0, 8).map((p) => (
              <div key={p.date} className="rounded border border-slate-200 p-2">
                <p>{p.date}</p>
                <p className="font-semibold text-slate-700">Avg {p.avg_aggregate}</p>
                <p>{p.sessions} sessions</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
