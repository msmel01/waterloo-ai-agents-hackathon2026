import { Link } from 'react-router-dom';
import { DashboardLayout } from '../../components/dashboard/DashboardLayout';
import { StatCard } from '../../components/dashboard/StatCard';
import { ScoreDistributionChart } from '../../components/dashboard/ScoreDistributionChart';
import { TrendChart } from '../../components/dashboard/TrendChart';
import { CategoryAverages } from '../../components/dashboard/CategoryAverages';
import { useDashboardStats } from '../../hooks/useDashboardStats';
import { useHeartStatus } from '../../hooks/useHeartStatus';

export function DashboardOverview() {
  const { statsQuery, trendsQuery } = useDashboardStats('daily', 30);
  const { statusQuery, toggleMutation } = useHeartStatus();

  const stats = statsQuery.data;
  const heartStatus = statusQuery.data;

  return (
    <DashboardLayout
      active={heartStatus?.active}
      loadingStatus={toggleMutation.isPending}
      onToggleStatus={(active) => toggleMutation.mutate(active)}
    >
      {statsQuery.isLoading ? (
        <p className="text-sm text-slate-500">Loading dashboard...</p>
      ) : stats ? (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <StatCard label="Suitors" value={stats.total_suitors} />
            <StatCard label="Dates" value={stats.total_dates} tone="positive" />
            <StatCard label="Match Rate" value={`${stats.match_rate.toFixed(1)}%`} tone="positive" />
            <StatCard label="Avg Score" value={stats.avg_scores.aggregate.toFixed(1)} tone="warning" />
            <StatCard label="Today" value={stats.recent_activity.sessions_today} />
            <StatCard label="Booked" value={stats.bookings.total_booked} />
            <StatCard label="Book Rate" value={`${stats.bookings.booking_rate.toFixed(1)}%`} tone="positive" />
            <StatCard label="Active Sessions" value={stats.active_sessions} tone="warning" />
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <ScoreDistributionChart data={stats.score_distribution} />
            <CategoryAverages values={stats.avg_scores} />
          </div>

          <TrendChart trend={trendsQuery.data} />

          <div>
            <Link
              to="/dashboard/sessions"
              className="inline-flex rounded border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100"
            >
              View All Sessions
            </Link>
          </div>
        </div>
      ) : (
        <p className="text-sm text-rose-600">Failed to load dashboard stats.</p>
      )}
    </DashboardLayout>
  );
}
