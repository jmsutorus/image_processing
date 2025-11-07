import { useMutation } from '@tanstack/react-query';
import { uploadBatch } from '@/lib/api';
import type { BatchConversionOptions, BatchSubmitResponse } from '@/lib/api';
import { toast } from 'sonner';
import { useState } from 'react';

interface BatchUploadParams {
  files: File[];
  options: BatchConversionOptions;
}

/**
 * Hook for uploading a batch of files for conversion
 * Returns the batch ID for polling status
 */
export function useBatch() {
  const [batchId, setBatchId] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: async ({ files, options }: BatchUploadParams): Promise<BatchSubmitResponse> => {
      return uploadBatch(files, options);
    },
    onSuccess: (data) => {
      setBatchId(data.batch_id);
      toast.success('Batch job submitted!', {
        description: `Processing ${data.total_files} files`,
      });
    },
    onError: (error: any) => {
      const errorMessage =
        error.response?.data?.detail ||
        error.message ||
        'Failed to submit batch job';

      toast.error('Batch upload failed', {
        description: errorMessage,
      });
    },
  });

  const resetBatch = () => {
    setBatchId(null);
  };

  return {
    uploadMutation: mutation,
    batchId,
    setBatchId,
    resetBatch,
  };
}
