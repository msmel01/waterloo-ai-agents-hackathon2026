import { useQuery } from '@tanstack/react-query';

import { getSlots } from '../api/results';

export function useSlots(
  sessionId: string,
  enabled: boolean,
  dateFrom?: string,
  dateTo?: string
) {
  return useQuery({
    queryKey: ['slots', sessionId, dateFrom, dateTo],
    queryFn: () => getSlots(sessionId, dateFrom, dateTo),
    enabled: Boolean(sessionId) && enabled,
    retry: 1,
  });
}
