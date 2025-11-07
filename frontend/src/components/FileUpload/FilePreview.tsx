import { useImagePreview } from '@/hooks/useImagePreview';
import { Card, CardContent } from '@/components/ui/card';
import { X, FileImage, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { formatFileSize } from '@/lib/validators';
import { canPreviewInBrowser } from '@/lib/fileUtils';

interface FilePreviewProps {
  file: File;
  onRemove: () => void;
  showRemove?: boolean;
}

export function FilePreview({ file, onRemove, showRemove = true }: FilePreviewProps) {
  const preview = useImagePreview(file);
  const isNonPreviewable = !canPreviewInBrowser(file);

  return (
    <Card className="relative">
      <CardContent className="p-4">
        {showRemove && (
          <Button
            variant="destructive"
            size="icon"
            className="absolute top-2 right-2 h-6 w-6 z-10"
            onClick={onRemove}
          >
            <X className="h-4 w-4" />
          </Button>
        )}
        <div className="space-y-2">
          {preview && !isNonPreviewable ? (
            <img
              src={preview}
              alt={file.name}
              className="w-full h-48 object-cover rounded"
            />
          ) : (
            <div className="w-full h-48 bg-muted rounded flex flex-col items-center justify-center gap-3 p-4">
              <FileImage className="h-12 w-12 text-muted-foreground" />
              {isNonPreviewable && (
                <div className="flex flex-col items-center gap-2 text-center">
                  <Badge variant="secondary" className="gap-1">
                    <AlertCircle className="h-3 w-3" />
                    Preview not available
                  </Badge>
                  <p className="text-xs text-muted-foreground max-w-[200px]">
                    HEIC and DNG previews are not supported by browsers, but your file is ready for conversion
                  </p>
                </div>
              )}
            </div>
          )}
          <div className="space-y-1">
            <p className="text-sm font-medium truncate" title={file.name}>
              {file.name}
            </p>
            <p className="text-xs text-muted-foreground">
              {formatFileSize(file.size)}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
