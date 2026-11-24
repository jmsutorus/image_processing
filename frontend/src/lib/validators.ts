import { z } from 'zod';

// File size limit: 200MB
const MAX_FILE_SIZE = 200 * 1024 * 1024;

// Accepted MIME types for image uploads
const ACCEPTED_IMAGE_TYPES = [
  'image/heic',
  'image/heif',
  'image/x-adobe-dng',
  'image/jpeg',
  'image/jpg',
  'image/png',
  'image/webp',
];

// Accepted file extensions
const ACCEPTED_EXTENSIONS = ['.heic', '.heif', '.dng', '.jpg', '.jpeg', '.png', '.webp'];

/**
 * Schema for single file conversion form
 */
export const convertFormSchema = z.object({
  outputFormat: z.enum(['jpeg', 'webp']),
  quality: z.number().min(0, 'Quality must be at least 0').max(100, 'Quality must be at most 100'),
  lossless: z.boolean(),
});

export type ConvertFormValues = z.infer<typeof convertFormSchema>;

/**
 * Validation result type
 */
export interface ValidationResult {
  success: boolean;
  error?: string;
}

/**
 * Validate a file for upload
 */
export function validateFile(file: File): ValidationResult {
  // Check file size
  if (file.size > MAX_FILE_SIZE) {
    return {
      success: false,
      error: `File size must be less than ${MAX_FILE_SIZE / 1024 / 1024}MB. File "${file.name}" is ${(file.size / 1024 / 1024).toFixed(2)}MB.`,
    };
  }

  // Check file extension
  const extension = `.${file.name.split('.').pop()?.toLowerCase()}`;
  if (!ACCEPTED_EXTENSIONS.includes(extension)) {
    return {
      success: false,
      error: `File type not supported. Only HEIC, DNG, JPEG, PNG, and WebP files are accepted. Got: ${extension}`,
    };
  }

  // Check MIME type if available
  if (file.type && !ACCEPTED_IMAGE_TYPES.includes(file.type)) {
    // Some browsers may not set the correct MIME type for HEIC/DNG
    // So we'll allow it if the extension is correct
    if (!ACCEPTED_EXTENSIONS.includes(extension)) {
      return {
        success: false,
        error: `Invalid file type: ${file.type}. Only HEIC, DNG, JPEG, PNG, and WebP files are supported.`,
      };
    }
  }

  return { success: true };
}

/**
 * Format file size for display
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}
