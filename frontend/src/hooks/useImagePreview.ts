import { useState, useEffect } from 'react';
import { canPreviewInBrowser } from '@/lib/fileUtils';

/**
 * Hook to create a preview URL for an image file
 * Automatically handles cleanup to prevent memory leaks
 * Returns null for HEIC and DNG files that can't be previewed in browsers
 */
export function useImagePreview(file: File | null): string | null {
  const [preview, setPreview] = useState<string | null>(null);

  useEffect(() => {
    if (!file) {
      setPreview(null);
      return;
    }

    // Don't create preview for formats that can't be displayed
    if (!canPreviewInBrowser(file)) {
      setPreview(null);
      return;
    }

    // Create object URL for preview
    const objectUrl = URL.createObjectURL(file);
    setPreview(objectUrl);

    // Cleanup: revoke the object URL when component unmounts or file changes
    return () => {
      URL.revokeObjectURL(objectUrl);
    };
  }, [file]);

  return preview;
}
