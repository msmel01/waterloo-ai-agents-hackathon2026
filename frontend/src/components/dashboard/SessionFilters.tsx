import type { SessionQueryParams } from '../../types/dashboard';

type Props = {
  filters: SessionQueryParams;
  onChange: (next: SessionQueryParams) => void;
};

export function SessionFilters({ filters, onChange }: Props) {
  return (
    <div className="grid gap-2 rounded-xl border border-slate-200 bg-white p-3 shadow-sm md:grid-cols-5">
      <input
        className="rounded border border-slate-300 px-3 py-2 text-sm"
        placeholder="Search by name..."
        value={filters.search || ''}
        onChange={(e) => onChange({ ...filters, page: 1, search: e.target.value })}
      />
      <select
        className="rounded border border-slate-300 px-3 py-2 text-sm"
        value={filters.verdict || ''}
        onChange={(e) => onChange({ ...filters, page: 1, verdict: e.target.value || undefined })}
      >
        <option value="">All verdicts</option>
        <option value="date">Date</option>
        <option value="no_date">No Date</option>
        <option value="pending">Pending</option>
      </select>
      <input
        type="date"
        className="rounded border border-slate-300 px-3 py-2 text-sm"
        value={filters.date_from || ''}
        onChange={(e) => onChange({ ...filters, page: 1, date_from: e.target.value || undefined })}
      />
      <input
        type="date"
        className="rounded border border-slate-300 px-3 py-2 text-sm"
        value={filters.date_to || ''}
        onChange={(e) => onChange({ ...filters, page: 1, date_to: e.target.value || undefined })}
      />
      <select
        className="rounded border border-slate-300 px-3 py-2 text-sm"
        value={`${filters.sort_by || 'date'}:${filters.sort_order || 'desc'}`}
        onChange={(e) => {
          const [sort_by, sort_order] = e.target.value.split(':');
          onChange({ ...filters, sort_by, sort_order });
        }}
      >
        <option value="date:desc">Newest</option>
        <option value="date:asc">Oldest</option>
        <option value="score:desc">Highest Score</option>
        <option value="score:asc">Lowest Score</option>
        <option value="name:asc">Name A-Z</option>
      </select>
    </div>
  );
}
