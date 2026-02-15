import { useQuery } from '@tanstack/react-query';
import { getSessions } from '../api/dashboard';
import type { SessionListResponse, SessionQueryParams } from '../types/dashboard';

export function useSessions(params: SessionQueryParams) {
  return useQuery<SessionListResponse>({
    queryKey: ['dashboard-sessions', params],
    queryFn: () => getSessions(params),
  });
}
