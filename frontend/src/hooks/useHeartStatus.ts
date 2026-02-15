import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { getHeartStatus, toggleHeartStatus } from '../api/dashboard';

export function useHeartStatus() {
  const queryClient = useQueryClient();
  const statusQuery = useQuery({
    queryKey: ['dashboard-heart-status'],
    queryFn: getHeartStatus,
    refetchInterval: 60_000,
  });

  const toggleMutation = useMutation({
    mutationFn: (active: boolean) => toggleHeartStatus(active),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboard-heart-status'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
    },
  });

  return { statusQuery, toggleMutation };
}
