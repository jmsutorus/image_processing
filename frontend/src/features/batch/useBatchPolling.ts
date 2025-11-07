import { useQuery } from '@tanstack/react-query';
import { getBatchStatus } from '@/lib/api';
import type { BatchStatusResponse } from '@/lib/api';

/**
 * Hook for polling batch job status
 * Automatically stops polling when batch is complete
 */
export function useBatchPolling(batchId: string | null) {
  return useQuery<BatchStatusResponse>({
    queryKey: ['batch', batchId],
    queryFn: () => {
      if (!batchId) throw new Error('No batch ID provided');
      return getBatchStatus(batchId);
    },
    enabled: !!batchId,
    refetchInterval: (query) => {
      const data = query.state.data;

      // Stop polling if batch is in a final state
      if (
        data?.status === 'SUCCESS' ||
        data?.status === 'FAILURE' ||
        data?.status === 'PARTIAL'
      ) {
        return false; // Stop polling
      }

      // Continue polling every 2 seconds
      return 2000;
    },
    staleTime: 0, // Always fetch fresh data
    retry: 3, // Retry failed requests
  });
}
