import { useQuery } from '@tanstack/react-query';
import { getStats, getTrends } from '../api/dashboard';

export function useDashboardStats(period: 'daily' | 'weekly' = 'daily', days = 30) {
  const statsQuery = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: getStats,
    refetchInterval: 60_000,
  });

  const trendsQuery = useQuery({
    queryKey: ['dashboard-trends', period, days],
    queryFn: () => getTrends(period, days),
    refetchInterval: 60_000,
  });

  return { statsQuery, trendsQuery };
}
