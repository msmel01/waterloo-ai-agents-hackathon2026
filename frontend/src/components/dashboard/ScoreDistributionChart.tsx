type Props = {
  data: {
    excellent: number;
    good: number;
    average: number;
    below_average: number;
  };
};

export function ScoreDistributionChart({ data }: Props) {
  const total = data.excellent + data.good + data.average + data.below_average || 1;
  const rows = [
    { label: 'Excellent (80+)', value: data.excellent, color: 'bg-green-500' },
    { label: 'Good (65-79)', value: data.good, color: 'bg-emerald-400' },
    { label: 'Average (50-64)', value: data.average, color: 'bg-amber-500' },
    { label: 'Below Average (<50)', value: data.below_average, color: 'bg-rose-500' },
  ];

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <h3 className="text-base font-semibold text-slate-900">Score Distribution</h3>
      <div className="mt-4 space-y-3">
        {rows.map((row) => (
          <div key={row.label}>
            <div className="mb-1 flex items-center justify-between text-sm text-slate-700">
              <span>{row.label}</span>
              <span className="font-semibold">{row.value}</span>
            </div>
            <div className="h-2 rounded-full bg-slate-100">
              <div
                className={`h-2 rounded-full ${row.color}`}
                style={{ width: `${(row.value / total) * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
