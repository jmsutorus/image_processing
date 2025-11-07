import { useDropzone } from 'react-dropzone';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Upload, FileImage, Shield } from 'lucide-react';

interface FileDropzoneProps {
  onFilesAccepted: (files: File[]) => void;
  maxFiles?: number;
  accept?: Record<string, string[]>;
  disabled?: boolean;
}

export function FileDropzone({
  onFilesAccepted,
  maxFiles = 1,
  accept = {
    'image/heic': ['.heic', '.heif'],
    'image/x-adobe-dng': ['.dng'],
    'image/jpeg': ['.jpg', '.jpeg'],
  },
  disabled = false,
}: FileDropzoneProps) {
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: onFilesAccepted,
    maxFiles,
    maxSize: 200 * 1024 * 1024, // 200MB
    accept,
    disabled,
  });

  return (
    <Card
      {...getRootProps()}
      className={`border-2 border-dashed p-8 cursor-pointer transition-colors ${
        isDragActive
          ? 'border-primary bg-primary/5'
          : 'border-muted-foreground/25 hover:border-muted-foreground/50'
      } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
    >
      <input {...getInputProps()} />
      <div className="flex flex-col items-center gap-4">
        <div className="relative">
          <Upload
            className={`h-12 w-12 ${
              isDragActive ? 'text-primary' : 'text-muted-foreground'
            }`}
          />
          {isDragActive && (
            <div className="absolute -top-1 -right-1">
              <div className="h-3 w-3 bg-primary rounded-full animate-pulse" />
            </div>
          )}
        </div>
        <div className="text-center space-y-3">
          <div>
            <p className="text-sm font-medium">
              {isDragActive
                ? 'Drop files here'
                : 'Drag & drop or click to upload'}
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              {maxFiles > 1 ? `Upload up to ${maxFiles} files` : 'Upload a single file'}
            </p>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-2">
            <Badge variant="secondary" className="gap-1">
              <FileImage className="h-3 w-3" />
              HEIC
            </Badge>
            <Badge variant="secondary" className="gap-1">
              <FileImage className="h-3 w-3" />
              DNG
            </Badge>
            <Badge variant="secondary" className="gap-1">
              <FileImage className="h-3 w-3" />
              JPEG
            </Badge>
          </div>

          <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground">
            <Shield className="h-3 w-3" />
            <span>Max 200MB per file • Metadata preserved</span>
          </div>
        </div>
      </div>
    </Card>
  );
}
