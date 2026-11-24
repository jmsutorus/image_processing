/**
 * Check if a file format can be previewed in the browser
 * HEIC, HEIF, and DNG files cannot be displayed natively in browsers
 */
export function canPreviewInBrowser(file: File): boolean {
  const extension = file.name.split('.').pop()?.toLowerCase();
  const nonPreviewableExtensions = ['heic', 'heif', 'dng'];

  // Check extension
  if (nonPreviewableExtensions.includes(extension || '')) {
    return false;
  }

  // Check MIME type
  if (
    file.type === 'image/heic' ||
    file.type === 'image/heif' ||
    file.type === 'image/x-adobe-dng'
  ) {
    return false;
  }

  return true;
}
