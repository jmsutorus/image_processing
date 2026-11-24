import axios from 'axios';

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 300000, // 5 minutes for large file uploads
});

export interface ConversionOptions {
  outputFormat: 'jpeg' | 'webp';
  quality?: number;
  lossless?: boolean;
  onProgress?: (progress: number) => void;
}

/**
 * Upload a single file for synchronous conversion
 */
export async function uploadForConversion(
  file: File,
  options: ConversionOptions
): Promise<Blob> {
  const formData = new FormData();
  formData.append('file', file);

  const endpoint = options.outputFormat === 'webp' ? '/convert-to-webp' : '/convert';

  const response = await apiClient.post(endpoint, formData, {
    params: {
      quality: options.quality || 85,
      lossless: options.lossless || false,
    },
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    responseType: 'blob',
    onUploadProgress: (progressEvent) => {
      if (progressEvent.total && options.onProgress) {
        const percent = Math.round(
          (progressEvent.loaded * 100) / progressEvent.total
        );
        options.onProgress(percent);
      }
    },
  });

  return response.data;
}
