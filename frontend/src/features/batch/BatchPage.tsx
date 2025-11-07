import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { FileDropzone, FilePreview } from '@/components/FileUpload';
import { batchFormSchema, validateFiles } from '@/lib/validators';
import type { BatchFormValues } from '@/lib/validators';
import { useBatch } from './useBatch';
import { BatchProgress } from './BatchProgress';
import { toast } from 'sonner';
import { Loader2, Trash2 } from 'lucide-react';

export function BatchPage() {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const { uploadMutation, batchId, resetBatch } = useBatch();

  const form = useForm<BatchFormValues>({
    resolver: zodResolver(batchFormSchema),
    defaultValues: {
      outputFormat: 'webp',
      quality: 85,
      lossless: false,
    },
  });

  const outputFormat = form.watch('outputFormat');

  const handleFilesAccepted = (files: File[]) => {
    if (files.length === 0) return;

    // Combine new files with existing files
    const allFiles = [...selectedFiles, ...files];

    // Validate combined files
    const validation = validateFiles(allFiles);

    if (!validation.success) {
      toast.error('Invalid files', {
        description: validation.error,
      });
      return;
    }

    setSelectedFiles(allFiles);
    toast.success(`${files.length} file(s) added`, {
      description: `Total: ${allFiles.length} file(s)`,
    });
  };

  const handleRemoveFile = (index: number) => {
    setSelectedFiles((files) => files.filter((_, i) => i !== index));
    toast.info('File removed');
  };

  const handleClearAll = () => {
    setSelectedFiles([]);
    toast.info('All files cleared');
  };

  const handleNewBatch = () => {
    resetBatch();
    setSelectedFiles([]);
    form.reset();
  };

  const onSubmit = (values: BatchFormValues) => {
    if (selectedFiles.length === 0) {
      toast.error('No files selected', {
        description: 'Please select at least one file to convert',
      });
      return;
    }

    uploadMutation.mutate({
      files: selectedFiles,
      options: {
        outputFormat: values.outputFormat,
        quality: values.quality,
        lossless: values.lossless,
      },
    });
  };

  // If batch is processing, show progress
  if (batchId) {
    return (
      <div className="w-full max-w-4xl mx-auto">
        <BatchProgress batchId={batchId} onNewBatch={handleNewBatch} />
      </div>
    );
  }

  const totalSize = selectedFiles.reduce((acc, file) => acc + file.size, 0);

  return (
    <div className="w-full max-w-4xl mx-auto space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Batch Conversion</CardTitle>
          <CardDescription>
            Convert multiple HEIC, DNG, and JPEG images at once (up to 50 files)
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* File Upload Section */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold">Select Files</h3>
              {selectedFiles.length > 0 && (
                <div className="flex items-center gap-2">
                  <span className="text-sm text-muted-foreground">
                    {selectedFiles.length} file(s) • {(totalSize / 1024 / 1024).toFixed(2)} MB
                  </span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleClearAll}
                    disabled={uploadMutation.isPending}
                  >
                    <Trash2 className="h-4 w-4 mr-1" />
                    Clear All
                  </Button>
                </div>
              )}
            </div>

            {selectedFiles.length === 0 ? (
              <FileDropzone
                onFilesAccepted={handleFilesAccepted}
                maxFiles={50}
                disabled={uploadMutation.isPending}
              />
            ) : (
              <>
                {/* File Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                  {selectedFiles.map((file, index) => (
                    <FilePreview
                      key={`${file.name}-${index}`}
                      file={file}
                      onRemove={() => handleRemoveFile(index)}
                      showRemove={!uploadMutation.isPending}
                    />
                  ))}
                </div>

                {/* Add More Files Button */}
                {selectedFiles.length < 50 && (
                  <FileDropzone
                    onFilesAccepted={handleFilesAccepted}
                    maxFiles={50 - selectedFiles.length}
                    disabled={uploadMutation.isPending}
                  />
                )}
              </>
            )}
          </div>

          {/* Conversion Options Form */}
          {selectedFiles.length > 0 && (
            <Form {...form}>
              <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
                <div className="rounded-lg border p-4 space-y-4">
                  <h3 className="text-sm font-semibold">Conversion Options</h3>
                  <p className="text-xs text-muted-foreground">
                    These settings will be applied to all {selectedFiles.length} file(s)
                  </p>

                  {/* Output Format */}
                  <FormField
                    control={form.control}
                    name="outputFormat"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Output Format</FormLabel>
                        <Select
                          onValueChange={field.onChange}
                          defaultValue={field.value}
                          disabled={uploadMutation.isPending}
                        >
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue placeholder="Select output format" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            <SelectItem value="jpeg">JPEG</SelectItem>
                            <SelectItem value="webp">WebP</SelectItem>
                          </SelectContent>
                        </Select>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  {/* Quality Slider */}
                  <FormField
                    control={form.control}
                    name="quality"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Quality: {field.value}%</FormLabel>
                        <FormControl>
                          <Slider
                            min={0}
                            max={100}
                            step={5}
                            value={[field.value]}
                            onValueChange={(value) => field.onChange(value[0])}
                            disabled={uploadMutation.isPending}
                            className="py-4"
                          />
                        </FormControl>
                        <FormDescription>
                          Higher quality produces larger files
                        </FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  {/* Lossless Toggle (WebP only) */}
                  {outputFormat === 'webp' && (
                    <FormField
                      control={form.control}
                      name="lossless"
                      render={({ field }) => (
                        <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                          <div className="space-y-0.5">
                            <FormLabel className="text-base">Lossless Compression</FormLabel>
                            <FormDescription>
                              Enable lossless compression for WebP (ignores quality setting)
                            </FormDescription>
                          </div>
                          <FormControl>
                            <Switch
                              checked={field.value}
                              onCheckedChange={field.onChange}
                              disabled={uploadMutation.isPending}
                            />
                          </FormControl>
                        </FormItem>
                      )}
                    />
                  )}
                </div>

                {/* Submit Button */}
                <Button
                  type="submit"
                  className="w-full"
                  disabled={uploadMutation.isPending}
                  size="lg"
                >
                  {uploadMutation.isPending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Uploading {selectedFiles.length} files...
                    </>
                  ) : (
                    `Convert ${selectedFiles.length} file(s)`
                  )}
                </Button>
              </form>
            </Form>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
