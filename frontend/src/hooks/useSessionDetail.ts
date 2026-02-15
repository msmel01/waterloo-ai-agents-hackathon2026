import { useQuery } from '@tanstack/react-query';
import { getSessionDetail } from '../api/dashboard';

export function useSessionDetail(sessionId: string | undefined) {
  return useQuery({
    queryKey: ['dashboard-session-detail', sessionId],
    queryFn: () => getSessionDetail(sessionId!),
    enabled: Boolean(sessionId),
  });
}
