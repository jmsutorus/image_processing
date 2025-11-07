import { useMutation } from '@tanstack/react-query';
import { uploadForConversion } from '@/lib/api';
import type { ConversionOptions } from '@/lib/api';
import { toast } from 'sonner';
import { useState } from 'react';

interface ConvertParams {
  file: File;
  options: ConversionOptions;
}

/**
 * Hook for converting a single file
 * Handles upload, progress tracking, and automatic download
 */
export function useConvert() {
  const [uploadProgress, setUploadProgress] = useState(0);

  const mutation = useMutation({
    mutationFn: async ({ file, options }: ConvertParams) => {
      return uploadForConversion(file, {
        ...options,
        onProgress: setUploadProgress,
      });
    },
    onSuccess: (blob, variables) => {
      // Create download link and trigger download
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;

      // Determine file extension based on output format
      const ext = variables.options.outputFormat === 'webp' ? 'webp' : 'jpg';
      const originalName = variables.file.name.split('.')[0];
      link.download = `${originalName}_converted.${ext}`;

      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      toast.success('Conversion successful!', {
        description: `Your file has been downloaded as ${originalName}_converted.${ext}`,
      });

      // Reset progress
      setUploadProgress(0);
    },
    onError: (error: any) => {
      const errorMessage =
        error.response?.data?.detail ||
        error.message ||
        'An unexpected error occurred';

      toast.error('Conversion failed', {
        description: errorMessage,
      });

      // Reset progress
      setUploadProgress(0);
    },
  });

  return {
    ...mutation,
    uploadProgress,
  };
}
