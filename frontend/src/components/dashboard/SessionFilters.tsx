import type { SessionQueryParams } from '../../types/dashboard';

type Props = {
  filters: SessionQueryParams;
  onChange: (next: SessionQueryParams) => void;
};

export function SessionFilters({ filters, onChange }: Props) {
  return (
    <div className="grid gap-2 rounded-xl border border-slate-200 bg-white p-3 shadow-sm md:grid-cols-5">
      <label htmlFor="search-input" className="sr-only">
        Search by suitor name
      </label>
      <input
        id="search-input"
        className="rounded border border-slate-300 px-3 py-2 text-sm"
        placeholder="Search by name..."
        value={filters.search || ''}
        onChange={(e) => onChange({ ...filters, page: 1, search: e.target.value })}
      />
      <label htmlFor="verdict-select" className="sr-only">
        Filter by verdict
      </label>
      <select
        id="verdict-select"
        className="rounded border border-slate-300 px-3 py-2 text-sm"
        value={filters.verdict || ''}
        onChange={(e) => onChange({ ...filters, page: 1, verdict: e.target.value || undefined })}
      >
        <option value="">All verdicts</option>
        <option value="date">Date</option>
        <option value="no_date">No Date</option>
        <option value="pending">Pending</option>
      </select>
      <label htmlFor="date-from-input" className="sr-only">
        Filter from date
      </label>
      <input
        id="date-from-input"
        type="date"
        className="rounded border border-slate-300 px-3 py-2 text-sm"
        value={filters.date_from || ''}
        onChange={(e) => onChange({ ...filters, page: 1, date_from: e.target.value || undefined })}
      />
      <label htmlFor="date-to-input" className="sr-only">
        Filter to date
      </label>
      <input
        id="date-to-input"
        type="date"
        className="rounded border border-slate-300 px-3 py-2 text-sm"
        value={filters.date_to || ''}
        onChange={(e) => onChange({ ...filters, page: 1, date_to: e.target.value || undefined })}
      />
      <label htmlFor="sort-select" className="sr-only">
        Sort sessions
      </label>
      <select
        id="sort-select"
        className="rounded border border-slate-300 px-3 py-2 text-sm"
        value={`${filters.sort_by || 'date'}:${filters.sort_order || 'desc'}`}
        onChange={(e) => {
          const [sort_by, sort_order] = e.target.value.split(':');
          onChange({ ...filters, sort_by, sort_order, page: 1 });
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
