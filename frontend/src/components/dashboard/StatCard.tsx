type StatCardProps = {
  label: string;
  value: string | number;
  tone?: 'neutral' | 'positive' | 'warning';
};

export function StatCard({ label, value, tone = 'neutral' }: StatCardProps) {
  const valueClass =
    tone === 'positive'
      ? 'text-green-600'
      : tone === 'warning'
        ? 'text-amber-600'
        : 'text-slate-900';

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <p className={`text-2xl font-bold ${valueClass}`}>{value}</p>
      <p className="mt-1 text-sm text-slate-500">{label}</p>
    </div>
  );
}
