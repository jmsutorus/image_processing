import { useBatchPolling } from './useBatchPolling';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { downloadBatchResults } from '@/lib/api';
import { toast } from 'sonner';
import { CheckCircle2, XCircle, Clock, Loader2, Download } from 'lucide-react';
import { formatFileSize } from '@/lib/validators';

interface BatchProgressProps {
  batchId: string;
  onNewBatch: () => void;
}

export function BatchProgress({ batchId, onNewBatch }: BatchProgressProps) {
  const { data: batchStatus, isLoading, error } = useBatchPolling(batchId);

  const handleDownload = async () => {
    try {
      await downloadBatchResults(batchId);
      toast.success('Download started', {
        description: 'Your converted files are being downloaded as a ZIP',
      });
    } catch (error: any) {
      toast.error('Download failed', {
        description: error.message || 'Failed to download results',
      });
    }
  };

  if (isLoading && !batchStatus) {
    return (
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <Skeleton className="h-6 w-32" />
            <Skeleton className="h-5 w-20" />
          </div>
          <Skeleton className="h-4 w-48 mt-2" />
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Skeleton className="h-4 w-28" />
              <Skeleton className="h-4 w-16" />
            </div>
            <Skeleton className="h-2 w-full" />
            <div className="flex gap-4">
              <Skeleton className="h-3 w-24" />
              <Skeleton className="h-3 w-20" />
              <Skeleton className="h-3 w-24" />
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center text-destructive">
            <XCircle className="h-8 w-8 mx-auto mb-2" />
            <p>Failed to load batch status</p>
            <p className="text-sm text-muted-foreground mt-1">
              {error instanceof Error ? error.message : 'Unknown error'}
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!batchStatus) {
    return null;
  }

  const isComplete =
    batchStatus.status === 'SUCCESS' ||
    batchStatus.status === 'FAILURE' ||
    batchStatus.status === 'PARTIAL';

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'SUCCESS':
        return (
          <Badge className="gap-1">
            <CheckCircle2 className="h-3 w-3" />
            Success
          </Badge>
        );
      case 'FAILURE':
        return (
          <Badge variant="destructive" className="gap-1">
            <XCircle className="h-3 w-3" />
            Failed
          </Badge>
        );
      case 'PROCESSING':
        return (
          <Badge variant="secondary" className="gap-1">
            <Loader2 className="h-3 w-3 animate-spin" />
            Processing
          </Badge>
        );
      case 'PENDING':
        return (
          <Badge variant="outline" className="gap-1">
            <Clock className="h-3 w-3" />
            Pending
          </Badge>
        );
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Batch Progress</span>
          {getStatusBadge(batchStatus.status)}
        </CardTitle>
        <CardDescription>Batch ID: {batchId.slice(0, 8)}...</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Overall Progress */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="font-medium">Overall Progress</span>
            <span className="text-muted-foreground">
              {batchStatus.completed + batchStatus.failed} / {batchStatus.total_files}
            </span>
          </div>
          <Progress value={batchStatus.percent} />
          <div className="flex gap-4 text-xs text-muted-foreground">
            <span className="flex items-center gap-1">
              <CheckCircle2 className="h-3 w-3 text-green-600" />
              {batchStatus.completed} completed
            </span>
            <span className="flex items-center gap-1">
              <XCircle className="h-3 w-3 text-red-600" />
              {batchStatus.failed} failed
            </span>
            <span className="flex items-center gap-1">
              <Clock className="h-3 w-3 text-yellow-600" />
              {batchStatus.pending} pending
            </span>
          </div>
        </div>

        {/* Individual Files */}
        {batchStatus.files && batchStatus.files.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-semibold">Files</h4>
            <div className="max-h-64 overflow-y-auto space-y-2 rounded-md border p-2">
              {batchStatus.files.map((file, index) => (
                <div
                  key={file.job_id || index}
                  className="flex items-center justify-between p-2 rounded-lg bg-muted/50"
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{file.filename}</p>
                    {file.size_bytes && (
                      <p className="text-xs text-muted-foreground">
                        {formatFileSize(file.size_bytes)}
                      </p>
                    )}
                    {file.error && (
                      <p className="text-xs text-destructive mt-1">{file.error}</p>
                    )}
                  </div>
                  <div className="ml-2">{getStatusBadge(file.status)}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-2">
          {isComplete && batchStatus.completed > 0 && (
            <Button onClick={handleDownload} className="flex-1 gap-2">
              <Download className="h-4 w-4" />
              Download ZIP ({batchStatus.completed} files)
            </Button>
          )}
          {isComplete && (
            <Button onClick={onNewBatch} variant="outline" className="flex-1">
              Start New Batch
            </Button>
          )}
        </div>

        {/* Status Message */}
        {batchStatus.message && (
          <p className="text-sm text-muted-foreground text-center">
            {batchStatus.message}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
