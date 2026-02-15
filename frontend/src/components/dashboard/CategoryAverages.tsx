type Props = {
  values: {
    effort: number;
    creativity: number;
    intent_clarity: number;
    emotional_intelligence: number;
  };
};

const rows: Array<{ key: keyof Props['values']; label: string }> = [
  { key: 'effort', label: 'Effort' },
  { key: 'creativity', label: 'Creativity' },
  { key: 'intent_clarity', label: 'Intent Clarity' },
  { key: 'emotional_intelligence', label: 'Emotional Intelligence' },
];

function tone(value: number) {
  if (value >= 80) return 'bg-green-500';
  if (value >= 65) return 'bg-amber-500';
  return 'bg-rose-500';
}

export function CategoryAverages({ values }: Props) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <h3 className="text-base font-semibold text-slate-900">Category Averages</h3>
      <div className="mt-4 space-y-3">
        {rows.map((row) => {
          const value = values[row.key] ?? 0;
          return (
            <div key={row.key}>
              <div className="mb-1 flex items-center justify-between text-sm">
                <span className="text-slate-700">{row.label}</span>
                <span className="font-semibold text-slate-900">{value.toFixed(1)}</span>
              </div>
              <div className="h-2 rounded-full bg-slate-100">
                <div
                  className={`h-2 rounded-full ${tone(value)}`}
                  style={{ width: `${Math.max(0, Math.min(100, value))}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
