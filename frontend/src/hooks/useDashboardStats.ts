import { useQuery } from '@tanstack/react-query';
import { getStats, getTrends } from '../api/dashboard';

export function useDashboardStats(period: 'daily' | 'weekly' = 'daily', days = 30) {
  const authKey = sessionStorage.getItem('dashboard_api_key');

  const statsQuery = useQuery({
    queryKey: ['dashboard-stats', authKey],
    queryFn: () => getStats(authKey ?? undefined),
    enabled: Boolean(authKey),
    refetchInterval: 60_000,
  });

  const trendsQuery = useQuery({
    queryKey: ['dashboard-trends', authKey, period, days],
    queryFn: () => getTrends(period, days, authKey ?? undefined),
    enabled: Boolean(authKey),
    refetchInterval: 60_000,
  });

  return { statsQuery, trendsQuery };
}
