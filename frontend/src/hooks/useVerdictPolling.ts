import { useQuery } from '@tanstack/react-query';

import { getVerdict } from '../api/results';

export function useVerdictPolling(sessionId: string) {
  return useQuery({
    queryKey: ['verdict', sessionId],
    queryFn: () => getVerdict(sessionId),
    enabled: Boolean(sessionId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === 'scored') {
        return false;
      }
      return 3000;
    },
    retry: false,
  });
}
