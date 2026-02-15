import { useMemo, useState } from 'react';
import { DashboardLayout } from '../../components/dashboard/DashboardLayout';
import { SessionFilters } from '../../components/dashboard/SessionFilters';
import { SessionCard } from '../../components/dashboard/SessionCard';
import { Pagination } from '../../components/dashboard/Pagination';
import { useSessions } from '../../hooks/useSessions';
import { useHeartStatus } from '../../hooks/useHeartStatus';
import type { SessionQueryParams } from '../../types/dashboard';

export function DashboardSessions() {
  const [filters, setFilters] = useState<SessionQueryParams>({
    page: 1,
    per_page: 20,
    sort_by: 'date',
    sort_order: 'desc',
  });
  const debouncedFilters = useMemo(() => filters, [filters]);
  const sessionsQuery = useSessions(debouncedFilters);
  const { statusQuery, toggleMutation } = useHeartStatus();

  const data = sessionsQuery.data;

  return (
    <DashboardLayout
      active={statusQuery.data?.active}
      loadingStatus={toggleMutation.isPending}
      onToggleStatus={(active) => toggleMutation.mutate(active)}
    >
      <h2 className="mb-3 text-xl font-semibold text-slate-900">All Sessions</h2>
      <SessionFilters filters={filters} onChange={setFilters} />
      {sessionsQuery.isLoading ? (
        <p className="mt-4 text-sm text-slate-500">Loading sessions...</p>
      ) : sessionsQuery.isError ? (
        <div className="mt-4 rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
          Failed to load sessions.
          {sessionsQuery.error instanceof Error && sessionsQuery.error.message
            ? ` ${sessionsQuery.error.message}`
            : ''}
        </div>
      ) : data && data.sessions.length > 0 ? (
        <>
          <div className="mt-4 space-y-3">
            {data.sessions.map((session) => (
              <SessionCard key={session.session_id} session={session} />
            ))}
          </div>
          <Pagination
            page={data.pagination.page}
            totalPages={data.pagination.total_pages}
            hasPrev={data.pagination.has_prev}
            hasNext={data.pagination.has_next}
            onChange={(page) => setFilters((prev) => ({ ...prev, page }))}
          />
        </>
      ) : (
        <p className="mt-4 rounded-xl border border-slate-200 bg-white p-6 text-sm text-slate-600">
          No sessions yet. Share your link to start screening suitors.
        </p>
      )}
    </DashboardLayout>
  );
}
