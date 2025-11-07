import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
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
import { convertFormSchema, validateFile } from '@/lib/validators';
import type { ConvertFormValues } from '@/lib/validators';
import { useConvert } from './useConvert';
import { toast } from 'sonner';
import { Loader2 } from 'lucide-react';

export function ConvertPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const { mutate, isPending, uploadProgress } = useConvert();

  const form = useForm<ConvertFormValues>({
    resolver: zodResolver(convertFormSchema),
    defaultValues: {
      outputFormat: 'webp',
      quality: 85,
      lossless: false,
    },
  });

  const outputFormat = form.watch('outputFormat');

  const handleFilesAccepted = (files: File[]) => {
    if (files.length === 0) return;

    const file = files[0];
    const validation = validateFile(file);

    if (!validation.success) {
      toast.error('Invalid file', {
        description: validation.error,
      });
      return;
    }

    setSelectedFile(file);
  };

  const handleRemoveFile = () => {
    setSelectedFile(null);
    form.reset();
  };

  const onSubmit = (values: ConvertFormValues) => {
    if (!selectedFile) {
      toast.error('No file selected', {
        description: 'Please select a file to convert',
      });
      return;
    }

    mutate(
      {
        file: selectedFile,
        options: {
          outputFormat: values.outputFormat,
          quality: values.quality,
          lossless: values.lossless,
        },
      },
      {
        onSuccess: () => {
          // Reset form and file selection after successful conversion
          setSelectedFile(null);
          form.reset();
        },
      }
    );
  };

  return (
    <div className="w-full max-w-2xl mx-auto space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Single File Conversion</CardTitle>
          <CardDescription>
            Convert HEIC, DNG, and JPEG images to JPEG or WebP format
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* File Upload Section */}
          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-semibold mb-2">Select File</h3>
              {!selectedFile ? (
                <FileDropzone onFilesAccepted={handleFilesAccepted} disabled={isPending} />
              ) : (
                <FilePreview file={selectedFile} onRemove={handleRemoveFile} />
              )}
            </div>
          </div>

          {/* Conversion Options Form */}
          {selectedFile && (
            <Form {...form}>
              <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
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
                        disabled={isPending}
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
                      <FormDescription>
                        Choose the output format for your converted image
                      </FormDescription>
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
                          disabled={isPending}
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
                            disabled={isPending}
                          />
                        </FormControl>
                      </FormItem>
                    )}
                  />
                )}

                {/* Progress Indicator */}
                {isPending && (
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Converting...</span>
                      <span className="font-medium">{uploadProgress}%</span>
                    </div>
                    <Progress value={uploadProgress} />
                  </div>
                )}

                {/* Submit Button */}
                <Button type="submit" className="w-full" disabled={isPending}>
                  {isPending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Converting...
                    </>
                  ) : (
                    'Convert Image'
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
