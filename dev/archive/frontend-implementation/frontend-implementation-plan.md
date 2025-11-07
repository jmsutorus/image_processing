# React + Tailwind + Shadcn Frontend Implementation Plan

**Last Updated: 2025-11-06**

---

## Executive Summary

This plan outlines the complete implementation of a modern, production-ready React frontend for the existing image processing service. The frontend will enable users to convert HEIC, DNG, and JPEG images to JPEG or WebP formats through an intuitive web interface.

### Key Deliverables
- Modern React 19 + TypeScript frontend using Vite
- Shadcn/ui component library with Tailwind CSS styling
- Single file conversion feature (synchronous)
- Batch file conversion feature (async with progress tracking)
- Responsive design for desktop and mobile
- Separate deployment-ready architecture

### Technology Stack
- **Frontend Framework**: Vite + React 19 + TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: Shadcn/ui (Radix UI primitives)
- **State Management**: TanStack Query (server state), React Hook Form (form state)
- **Validation**: Zod schemas
- **File Upload**: react-dropzone
- **HTTP Client**: Axios
- **Routing**: React Router 7
- **Notifications**: Sonner (toast library)

### Timeline
- **Estimated Effort**: 14-21 hours of focused development
- **Duration**: 2-3 days with dedicated work
- **Phases**: 7 implementation phases

---

## Current State Analysis

### Backend API (Fully Implemented)
The FastAPI backend at `backend/app.py` provides comprehensive REST endpoints:

#### Synchronous Endpoints (Phase 1)
- `POST /convert` - HEIC/DNG/JPG → JPEG (blocking, immediate response)
- `POST /convert-to-webp` - HEIC/DNG/JPG → WebP (blocking, immediate response)
  - Parameters: `lossless` (bool), `quality` (0-100)

#### Asynchronous Endpoints (Phase 2)
- `POST /jobs/convert` - Submit async job, returns `job_id`
- `GET /jobs/{job_id}` - Poll job status
- `GET /jobs/{job_id}/result` - Download converted image

#### Batch Processing Endpoints
- `POST /jobs/batch-convert` - Upload multiple files (max 50), returns `batch_id`
- `GET /jobs/batch/{batch_id}` - Check batch progress and individual file statuses
- `GET /jobs/batch/{batch_id}/results` - Download ZIP of all successful conversions

#### Validation & Constraints
- **Max file size**: 200MB per file
- **Supported input**: `.heic`, `.heif`, `.dng`, `.jpg`, `.jpeg`
- **Output formats**: `jpeg`, `webp`
- **MIME type validation**: Magic number checking for security
- **Batch limit**: 25 files maximum

### Current Limitations
- **No frontend UI**: Service is API-only
- **Access method**: curl, Postman, or Swagger docs at `/docs`
- **User experience**: Technical users only, no visual interface
- **Deployment**: Backend containerized with Docker, frontend not yet created

### Infrastructure
- **Backend**: FastAPI + Celery + Redis
- **Workers**: 2 concurrent Celery workers
- **Result storage**: Redis with 1-hour TTL
- **Container**: Non-root user (UID 1000), security hardened

---

## Proposed Future State

### User Experience Vision

#### Landing Page
Users arrive at a clean, modern interface with:
- **Header**: Application title and logo
- **Tab Navigation**: Switch between "Single File" and "Batch Upload" modes
- **Instructions**: Clear guidance on supported formats and features

#### Single File Conversion Flow
1. **Upload Area**: Drag-and-drop zone with click-to-select fallback
2. **File Preview**: Thumbnail preview of selected image with metadata (name, size)
3. **Conversion Options**:
   - Output format selector (JPEG / WebP)
   - Quality slider (0-100) with visual feedback
   - Lossless toggle for WebP
4. **Submit**: Convert button triggers upload
5. **Progress**: Upload progress bar with percentage
6. **Result**: Automatic download on completion + success notification

#### Batch Conversion Flow
1. **Multi-Upload Area**: Drag-and-drop for multiple files (up to 50)
2. **File Grid**: Thumbnail grid showing all selected images
   - Individual file removal buttons
   - Clear all button
   - File count and total size display
3. **Shared Options**: Single set of conversion settings for all files
4. **Batch Submit**: Upload all files simultaneously
5. **Progress Tracking**:
   - Overall progress bar
   - Individual file status indicators
   - Completed/Failed/Processing counts
6. **Download**: Download ZIP button when batch completes

### Technical Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Vite + React)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Convert    │  │    Batch     │  │   Layout     │     │
│  │   Feature    │  │   Feature    │  │  Components  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         TanStack Query (API State Management)        │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │      Axios API Client (HTTP Communication)           │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                             │
                             │ CORS-enabled HTTP
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                 Backend (FastAPI + Celery)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Sync API    │  │  Async API   │  │  Batch API   │     │
│  │  /convert    │  │ /jobs/convert│  │/jobs/batch   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Celery Workers + Redis (Job Queue)           │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Deployment Strategy
- **Frontend**: Deploy to Vercel/Netlify (static hosting)
- **Backend**: Existing Docker container on cloud server
- **Communication**: CORS-enabled API calls
- **Environment**: Frontend URL configured in backend CORS allowlist

---

## Implementation Phases

### Phase 1: Project Initialization & Setup
**Duration: 1-2 hours**

#### Tasks
1. **Create Vite project**
   ```bash
   npm create vite@latest frontend -- --template react-ts
   cd frontend
   npm install
   ```

2. **Install core dependencies**
   ```bash
   npm install react-router-dom @tanstack/react-query axios react-hook-form @hookform/resolvers zod react-dropzone sonner lucide-react class-variance-authority clsx tailwind-merge
   ```

3. **Configure Tailwind CSS**
   ```bash
   npm install -D tailwindcss postcss autoprefixer
   npx tailwindcss init -p
   ```
   - Update `tailwind.config.js` with content paths
   - Add Tailwind directives to `index.css`

4. **Initialize Shadcn/ui**
   ```bash
   npx shadcn@latest init
   ```
   - Choose: New York style, Slate color, CSS variables
   - Configure `components.json` for TypeScript + Vite

5. **Install Shadcn components**
   ```bash
   npx shadcn@latest add button card input form progress tabs select slider switch badge toast
   ```

6. **Configure backend CORS**
   - Edit `backend/app.py`
   - Add CORS middleware:
   ```python
   from fastapi.middleware.cors import CORSMiddleware

   app.add_middleware(
       CORSMiddleware,
       allow_origins=[
           "http://localhost:5173",  # Vite dev
           "http://localhost:3000",  # Alternative
       ],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

#### Acceptance Criteria
- [ ] Vite dev server runs on `http://localhost:5173`
- [ ] Tailwind CSS compiles successfully
- [ ] Shadcn components render without errors
- [ ] Backend accepts CORS requests from frontend

---

### Phase 2: Core Infrastructure
**Duration: 2-3 hours**

#### Tasks

1. **Create API client (`src/lib/api.ts`)**
   ```typescript
   import axios from 'axios';

   export const apiClient = axios.create({
     baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
     timeout: 300000, // 5 minutes
   });

   export async function uploadForConversion(
     file: File,
     options: {
       outputFormat: 'jpeg' | 'webp';
       quality?: number;
       lossless?: boolean;
       onProgress?: (progress: number) => void;
     }
   ) {
     const formData = new FormData();
     formData.append('file', file);

     const response = await apiClient.post(
       `/convert${options.outputFormat === 'webp' ? '-to-webp' : ''}`,
       formData,
       {
         params: {
           quality: options.quality || 85,
           lossless: options.lossless || false,
         },
         headers: {
           'Content-Type': 'multipart/form-data',
         },
         responseType: 'blob',
         onUploadProgress: (progressEvent) => {
           if (progressEvent.total) {
             const percent = Math.round(
               (progressEvent.loaded * 100) / progressEvent.total
             );
             options.onProgress?.(percent);
           }
         },
       }
     );

     return response.data;
   }

   export async function uploadBatch(
     files: File[],
     options: {
       outputFormat: 'jpeg' | 'webp';
       quality?: number;
       lossless?: boolean;
     }
   ) {
     const formData = new FormData();
     files.forEach(file => {
       formData.append('files', file);
     });

     const response = await apiClient.post(
       `/jobs/batch-convert`,
       formData,
       {
         params: {
           output_format: options.outputFormat,
           quality: options.quality || 85,
           lossless: options.lossless || false,
         },
         headers: {
           'Content-Type': 'multipart/form-data',
         },
       }
     );

     return response.data;
   }

   export async function getBatchStatus(batchId: string) {
     const response = await apiClient.get(`/jobs/batch/${batchId}`);
     return response.data;
   }

   export async function downloadBatchResults(batchId: string) {
     const response = await apiClient.get(
       `/jobs/batch/${batchId}/results`,
       { responseType: 'blob' }
     );

     const url = URL.createObjectURL(response.data);
     const link = document.createElement('a');
     link.href = url;
     link.download = `batch_${batchId.slice(0, 8)}_results.zip`;
     link.click();
     URL.revokeObjectURL(url);
   }
   ```

2. **Create Zod validation schemas (`src/lib/validators.ts`)**
   ```typescript
   import { z } from 'zod';

   const MAX_FILE_SIZE = 200 * 1024 * 1024; // 200MB
   const ACCEPTED_IMAGE_TYPES = [
     'image/heic',
     'image/heif',
     'image/x-adobe-dng',
     'image/jpeg',
   ];

   export const convertFormSchema = z.object({
     outputFormat: z.enum(['jpeg', 'webp']),
     quality: z.number().min(0).max(100).default(85),
     lossless: z.boolean().default(false),
   });

   export const batchFormSchema = z.object({
     outputFormat: z.enum(['jpeg', 'webp']),
     quality: z.number().min(0).max(100).default(85),
     lossless: z.boolean().default(false),
   });

   export function validateFile(file: File): { success: boolean; error?: string } {
     if (file.size > MAX_FILE_SIZE) {
       return {
         success: false,
         error: `File size must be less than ${MAX_FILE_SIZE / 1024 / 1024}MB`,
       };
     }

     if (!ACCEPTED_IMAGE_TYPES.includes(file.type)) {
       return {
         success: false,
         error: 'Only HEIC, DNG, and JPEG files are supported',
       };
     }

     return { success: true };
   }
   ```

3. **Set up TanStack Query (`src/main.tsx`)**
   ```typescript
   import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

   const queryClient = new QueryClient({
     defaultOptions: {
       queries: {
         staleTime: 0,
         refetchOnWindowFocus: false,
       },
     },
   });

   createRoot(document.getElementById('root')!).render(
     <StrictMode>
       <QueryClientProvider client={queryClient}>
         <App />
       </QueryClientProvider>
     </StrictMode>,
   );
   ```

4. **Create FileDropzone component (`src/components/FileUpload/FileDropzone.tsx`)**
   ```typescript
   import { useDropzone } from 'react-dropzone';
   import { Card } from '@/components/ui/card';
   import { Upload } from 'lucide-react';

   interface FileDropzoneProps {
     onFilesAccepted: (files: File[]) => void;
     maxFiles?: number;
     accept?: Record<string, string[]>;
   }

   export function FileDropzone({
     onFilesAccepted,
     maxFiles = 1,
     accept = {
       'image/heic': ['.heic', '.heif'],
       'image/x-adobe-dng': ['.dng'],
       'image/jpeg': ['.jpg', '.jpeg'],
     },
   }: FileDropzoneProps) {
     const { getRootProps, getInputProps, isDragActive } = useDropzone({
       onDrop: onFilesAccepted,
       maxFiles,
       maxSize: 200 * 1024 * 1024,
       accept,
     });

     return (
       <Card
         {...getRootProps()}
         className={`border-2 border-dashed p-8 cursor-pointer transition-colors
           ${isDragActive ? 'border-primary bg-primary/5' : 'border-muted-foreground/25'}`}
       >
         <input {...getInputProps()} />
         <div className="flex flex-col items-center gap-4">
           <Upload className="h-12 w-12 text-muted-foreground" />
           <div className="text-center">
             <p className="text-sm font-medium">
               {isDragActive ? 'Drop files here' : 'Drag & drop or click to upload'}
             </p>
             <p className="text-xs text-muted-foreground mt-1">
               HEIC, DNG, JPEG (max 200MB)
             </p>
           </div>
         </div>
       </Card>
     );
   }
   ```

5. **Create FilePreview component (`src/components/FileUpload/FilePreview.tsx`)**
   ```typescript
   import { useImagePreview } from '@/hooks/useImagePreview';
   import { Card, CardContent } from '@/components/ui/card';
   import { X } from 'lucide-react';
   import { Button } from '@/components/ui/button';

   interface FilePreviewProps {
     file: File;
     onRemove: () => void;
   }

   export function FilePreview({ file, onRemove }: FilePreviewProps) {
     const preview = useImagePreview(file);

     return (
       <Card className="relative">
         <CardContent className="p-4">
           <Button
             variant="destructive"
             size="icon"
             className="absolute top-2 right-2 h-6 w-6"
             onClick={onRemove}
           >
             <X className="h-4 w-4" />
           </Button>
           {preview && (
             <img
               src={preview}
               alt={file.name}
               className="w-full h-48 object-cover rounded"
             />
           )}
           <p className="text-sm font-medium mt-2 truncate">{file.name}</p>
           <p className="text-xs text-muted-foreground">
             {(file.size / 1024 / 1024).toFixed(2)} MB
           </p>
         </CardContent>
       </Card>
     );
   }
   ```

6. **Create useImagePreview hook (`src/hooks/useImagePreview.ts`)**
   ```typescript
   import { useState, useEffect } from 'react';

   export function useImagePreview(file: File | null) {
     const [preview, setPreview] = useState<string | null>(null);

     useEffect(() => {
       if (!file) {
         setPreview(null);
         return;
       }

       const objectUrl = URL.createObjectURL(file);
       setPreview(objectUrl);

       return () => URL.revokeObjectURL(objectUrl);
     }, [file]);

     return preview;
   }
   ```

#### Acceptance Criteria
- [ ] API client successfully makes requests to backend
- [ ] File validation works with Zod schemas
- [ ] TanStack Query provider wraps application
- [ ] FileDropzone accepts drag-and-drop and click uploads
- [ ] FilePreview shows image thumbnail and metadata
- [ ] Image preview uses URL.createObjectURL (no memory leaks)

---

### Phase 3: Single File Conversion Feature
**Duration: 3-4 hours**

#### Tasks

1. **Create ConvertPage component (`src/features/convert/ConvertPage.tsx`)**
   - Form with FileDropzone
   - Output format selector (Select component)
   - Quality slider (Slider component)
   - Lossless toggle (Switch component)
   - Submit button
   - Progress indicator during upload
   - Success/error toast notifications

2. **Implement conversion mutation hook (`src/features/convert/useConvert.ts`)**
   ```typescript
   import { useMutation } from '@tanstack/react-query';
   import { uploadForConversion } from '@/lib/api';
   import { toast } from 'sonner';
   import { useState } from 'react';

   export function useConvert() {
     const [uploadProgress, setUploadProgress] = useState(0);

     const mutation = useMutation({
       mutationFn: ({
         file,
         options,
       }: {
         file: File;
         options: {
           outputFormat: 'jpeg' | 'webp';
           quality?: number;
           lossless?: boolean;
         };
       }) =>
         uploadForConversion(file, {
           ...options,
           onProgress: setUploadProgress,
         }),
       onSuccess: (blob, variables) => {
         // Trigger download
         const url = URL.createObjectURL(blob);
         const link = document.createElement('a');
         link.href = url;
         const ext = variables.options.outputFormat === 'webp' ? 'webp' : 'jpg';
         link.download = `converted.${ext}`;
         link.click();
         URL.revokeObjectURL(url);

         toast.success('Conversion successful!', {
           description: 'Your file has been downloaded.',
         });
         setUploadProgress(0);
       },
       onError: (error: any) => {
         toast.error('Conversion failed', {
           description: error.response?.data?.detail || error.message,
         });
         setUploadProgress(0);
       },
     });

     return {
       ...mutation,
       uploadProgress,
     };
   }
   ```

3. **Add form validation with react-hook-form**
   - Use `useForm` with `zodResolver(convertFormSchema)`
   - Wire up form fields with `Controller` components
   - Display validation errors

4. **Implement automatic download**
   - Create blob URL from response
   - Trigger browser download
   - Revoke object URL to prevent memory leaks

5. **Add progress indicator**
   - Show Progress component during upload
   - Display percentage from upload progress callback

#### Acceptance Criteria
- [ ] Users can select a file via drag-and-drop or click
- [ ] File preview appears with thumbnail and metadata
- [ ] Output format can be selected (JPEG/WebP)
- [ ] Quality slider adjusts value (0-100)
- [ ] Lossless toggle works for WebP
- [ ] Submit button triggers conversion
- [ ] Upload progress bar shows during upload
- [ ] Success notification appears on completion
- [ ] File automatically downloads when ready
- [ ] Error notifications show meaningful messages
- [ ] Form resets after successful conversion

---

### Phase 4: Batch Conversion Feature
**Duration: 3-4 hours**

#### Tasks

1. **Create BatchPage component (`src/features/batch/BatchPage.tsx`)**
   - Multi-file dropzone (maxFiles: 50)
   - Grid display of selected files with previews
   - Shared conversion options
   - Submit button for batch upload
   - Batch progress tracking

2. **Implement batch upload mutation (`src/features/batch/useBatch.ts`)**
   ```typescript
   import { useMutation, useQuery } from '@tanstack/react-query';
   import { uploadBatch, getBatchStatus } from '@/lib/api';
   import { toast } from 'sonner';
   import { useState } from 'react';

   export function useBatch() {
     const [batchId, setBatchId] = useState<string | null>(null);

     const uploadMutation = useMutation({
       mutationFn: uploadBatch,
       onSuccess: (data) => {
         setBatchId(data.batch_id);
         toast.success('Batch job submitted!', {
           description: `Processing ${data.total_files} files`,
         });
       },
       onError: (error: any) => {
         toast.error('Batch upload failed', {
           description: error.response?.data?.detail || error.message,
         });
       },
     });

     return {
       uploadMutation,
       batchId,
       setBatchId,
     };
   }
   ```

3. **Create BatchProgress component (`src/features/batch/BatchProgress.tsx`)**
   - Poll batch status every 2 seconds
   - Display overall progress bar
   - Show individual file statuses in a list
   - Display completed/failed/processing counts
   - Download ZIP button when complete

4. **Implement batch status polling**
   ```typescript
   export function useBatchPolling(batchId: string | null) {
     return useQuery({
       queryKey: ['batch', batchId],
       queryFn: () => getBatchStatus(batchId!),
       enabled: !!batchId,
       refetchInterval: (data) => {
         if (data?.status === 'SUCCESS' || data?.status === 'FAILURE' || data?.status === 'PARTIAL') {
           return false; // Stop polling
         }
         return 2000; // Poll every 2 seconds
       },
       staleTime: 0,
     });
   }
   ```

5. **Add file management features**
   - Remove individual files before upload
   - Clear all files button
   - Display file count and total size
   - Show validation errors per file

6. **Implement ZIP download**
   - Download button triggers `downloadBatchResults()`
   - Blob download with proper filename

#### Acceptance Criteria
- [ ] Users can select multiple files (up to 50)
- [ ] File grid displays all selected files with thumbnails
- [ ] Individual files can be removed before upload
- [ ] Clear all button removes all files
- [ ] Shared conversion options apply to all files
- [ ] Submit button uploads all files as batch
- [ ] Batch ID displayed after successful upload
- [ ] Progress component shows overall progress
- [ ] Individual file statuses displayed (pending/processing/success/failure)
- [ ] Completed/Failed/Processing counts update in real-time
- [ ] Download ZIP button appears when batch completes
- [ ] ZIP download triggers and saves locally
- [ ] Error handling shows which files failed

---

### Phase 5: UI Polish & Layout
**Duration: 2-3 hours**

#### Tasks

1. **Create Header component (`src/components/Layout/Header.tsx`)**
   - Application title and logo
   - Simple, clean design
   - Responsive layout

2. **Create Footer component (`src/components/Layout/Footer.tsx`)**
   - Copyright notice
   - Links (if any)
   - Minimal design

3. **Implement tabbed interface**
   - Use Shadcn Tabs component
   - Tabs: "Single File" and "Batch Upload"
   - Tab content switches between ConvertPage and BatchPage

4. **Add loading skeletons**
   - Use Shadcn Skeleton component
   - Show during initial load
   - Better perceived performance

5. **Enhance toast notifications**
   - Configure Sonner position (bottom-right)
   - Customize toast appearance
   - Add icons for success/error states

6. **Create error boundary**
   - Catch React errors gracefully
   - Display friendly error message
   - Provide reset/reload option

7. **Improve drag-and-drop feedback**
   - Border color changes on drag-over
   - Visual indication of accepted files
   - Smooth transitions

8. **Add helpful UI elements**
   - Badge showing supported formats in dropzone
   - File size limits prominently displayed
   - Conversion tips or instructions
   - Empty state messages

9. **Responsive design improvements**
   - Mobile-first approach
   - Test on various screen sizes
   - Ensure touch interactions work
   - Adjust grid layouts for mobile

#### Acceptance Criteria
- [ ] Header renders with title and logo
- [ ] Footer renders with copyright
- [ ] Tabs switch between Single and Batch modes
- [ ] Tab state persists during session
- [ ] Loading skeletons appear during data fetching
- [ ] Toast notifications styled consistently
- [ ] Error boundary catches and displays errors
- [ ] Drag-and-drop shows visual feedback
- [ ] Supported formats badge visible in dropzone
- [ ] File size limits clearly displayed
- [ ] Empty states show helpful messages
- [ ] Responsive design works on mobile (375px+)
- [ ] Touch interactions work on tablets/phones

---

### Phase 6: Environment & Deployment Setup
**Duration: 1-2 hours**

#### Tasks

1. **Create environment files**
   - `.env.development`:
     ```
     VITE_API_URL=http://localhost:8000
     ```
   - `.env.production`:
     ```
     VITE_API_URL=https://api.yourdomain.com
     ```
   - Add `.env*` to `.gitignore` (keep `.env.example`)

2. **Configure Vite for environment variables**
   - Update `vite.config.ts`:
   ```typescript
   import { defineConfig } from 'vite';
   import react from '@vitejs/plugin-react';
   import path from 'path';

   export default defineConfig({
     plugins: [react()],
     resolve: {
       alias: {
         '@': path.resolve(__dirname, './src'),
       },
     },
     server: {
       port: 5173,
     },
   });
   ```

3. **Update backend CORS for production**
   - Edit `backend/app.py`
   - Add production frontend URL to `allow_origins`
   - Example: `https://yourapp.vercel.app`

4. **Create deployment documentation**
   - `frontend/README.md` with:
     - Setup instructions
     - Development commands
     - Build commands
     - Environment variable documentation
     - Deployment steps for Vercel/Netlify

5. **Create `.env.example`**
   ```
   VITE_API_URL=http://localhost:8000
   ```

6. **Test production build**
   ```bash
   npm run build
   npm run preview
   ```

7. **Create `vercel.json` or `netlify.toml`**
   - Configure build settings
   - Set environment variables
   - Configure SPA routing (all routes → index.html)

#### Acceptance Criteria
- [ ] Environment variables work in development
- [ ] Environment variables work in production build
- [ ] Backend CORS accepts production frontend URL
- [ ] README documents all setup steps
- [ ] `.env.example` provided for reference
- [ ] Production build succeeds without errors
- [ ] Preview server works with production build
- [ ] Deployment configuration files created
- [ ] SPA routing works (no 404s on refresh)

---

### Phase 7: Testing & Refinement
**Duration: 2-3 hours**

#### Tasks

1. **Functional testing**
   - Test HEIC file upload and conversion
   - Test DNG file upload and conversion
   - Test JPEG file upload and conversion
   - Test JPEG output format
   - Test WebP output format (lossy)
   - Test WebP output format (lossless)
   - Test quality slider (various values)
   - Test batch upload (2, 10, 50 files)
   - Test batch download (ZIP file)

2. **Error scenario testing**
   - Test file size over 200MB (should show error)
   - Test invalid file type (should show error)
   - Test network error (should show error toast)
   - Test backend unavailable (should show error)
   - Test batch with some failed files
   - Test rapid re-uploads

3. **Browser compatibility testing**
   - Chrome (latest)
   - Firefox (latest)
   - Safari (latest)
   - Edge (latest)

4. **Responsive design testing**
   - Mobile (375px - iPhone SE)
   - Mobile (390px - iPhone 12/13/14)
   - Tablet (768px - iPad)
   - Desktop (1024px+)
   - Large desktop (1920px+)

5. **Performance testing**
   - Test with large files (close to 200MB)
   - Test batch with 50 files
   - Check for memory leaks (URL.revokeObjectURL)
   - Verify image previews don't slow down UI
   - Check bundle size (`npm run build` output)

6. **Accessibility testing**
   - Keyboard navigation works
   - Screen reader compatibility
   - Focus indicators visible
   - ARIA labels present
   - Color contrast sufficient

7. **Bug fixes and polish**
   - Fix any issues discovered
   - Improve error messages
   - Refine animations and transitions
   - Optimize performance

#### Acceptance Criteria
- [ ] All file types convert successfully
- [ ] Both output formats work correctly
- [ ] Quality and lossless options affect output
- [ ] Batch processing works with various file counts
- [ ] All error scenarios handled gracefully
- [ ] Works in all major browsers
- [ ] Responsive on all device sizes
- [ ] No memory leaks detected
- [ ] Good performance with large files
- [ ] Keyboard navigation works
- [ ] Screen reader accessible
- [ ] No console errors or warnings

---

## Risk Assessment & Mitigation

### Technical Risks

| Risk | Likelihood | Impact | Mitigation Strategy |
|------|------------|--------|---------------------|
| CORS configuration issues | Medium | High | Test CORS early; document exact configuration; use proper middleware |
| File upload failures with large files | Medium | Medium | Implement upload timeout; show clear progress; handle network errors |
| Memory leaks from image previews | Low | Medium | Always use URL.revokeObjectURL; test with many files |
| Browser compatibility issues | Low | Medium | Test in all major browsers; use standard APIs; avoid experimental features |
| Bundle size too large | Low | Low | Use code splitting; lazy load routes; analyze bundle with Vite tools |

### User Experience Risks

| Risk | Likelihood | Impact | Mitigation Strategy |
|------|------------|--------|---------------------|
| Confusing file format support | Medium | Medium | Clear messaging in UI; visual indicators; helpful error messages |
| Unclear conversion progress | Low | High | Prominent progress bars; percentage display; status messages |
| Batch download confusion | Medium | Medium | Clear instructions; prominent download button; success confirmation |
| Mobile usability issues | Medium | High | Mobile-first design; touch-friendly targets; responsive testing |

### Deployment Risks

| Risk | Likelihood | Impact | Mitigation Strategy |
|------|------------|--------|---------------------|
| Environment variable misconfiguration | High | High | Document thoroughly; use .env.example; validate at build time |
| API URL mismatch in production | Medium | High | Test production build locally; verify CORS; check network requests |
| SPA routing breaks on refresh | Medium | Medium | Configure server (Vercel/Netlify) for SPA; test all routes |

---

## Success Metrics

### Functional Metrics
- ✅ Users can convert single files in < 5 clicks
- ✅ Batch upload supports up to 50 files simultaneously
- ✅ All supported formats convert successfully (HEIC, DNG, JPEG)
- ✅ Both output formats work (JPEG, WebP)
- ✅ Conversion quality controls function correctly
- ✅ Error messages are clear and actionable

### Performance Metrics
- ✅ Initial page load < 2 seconds
- ✅ Time to interactive < 3 seconds
- ✅ Upload progress updates at least every 500ms
- ✅ No memory leaks with 50+ file previews
- ✅ Bundle size < 500KB (gzipped)

### User Experience Metrics
- ✅ Mobile-responsive (works on 375px+ screens)
- ✅ Keyboard navigation fully functional
- ✅ Screen reader compatible
- ✅ Toast notifications appear for all actions
- ✅ Progress indicators visible during all async operations

### Technical Metrics
- ✅ Zero console errors in production
- ✅ 100% TypeScript type coverage
- ✅ Lighthouse score > 90 (Performance, Accessibility, Best Practices)
- ✅ Works in Chrome, Firefox, Safari, Edge (latest versions)

---

## Required Resources & Dependencies

### Development Environment
- **Node.js**: v18+ (for Vite and modern React)
- **npm**: v9+ (package management)
- **Git**: Version control
- **Code editor**: VS Code (recommended)

### External Services
- **Backend API**: FastAPI server running on localhost:8000 (dev) or production URL
- **CORS**: Backend must have CORS configured for frontend origin

### Third-Party Libraries
All dependencies managed via npm (see `package.json`):
- **Core**: react, react-dom, typescript
- **Build**: vite, @vitejs/plugin-react
- **Styling**: tailwindcss, postcss, autoprefixer
- **UI**: @radix-ui/* (via shadcn), lucide-react
- **State**: @tanstack/react-query, react-hook-form
- **Validation**: zod, @hookform/resolvers
- **HTTP**: axios
- **File Upload**: react-dropzone
- **Notifications**: sonner
- **Utils**: class-variance-authority, clsx, tailwind-merge

### Deployment Platform (Choose One)
- **Vercel** (recommended): Automatic deployment from Git, environment variables, edge network
- **Netlify**: Similar features, good Vite support
- **Other static hosts**: GitHub Pages, Cloudflare Pages, etc.

---

## Timeline Estimates

### Detailed Breakdown

| Phase | Tasks | Estimated Hours | Cumulative |
|-------|-------|-----------------|------------|
| Phase 1: Setup | Project init, Tailwind, Shadcn, CORS | 1-2 | 1-2 |
| Phase 2: Infrastructure | API client, validation, hooks, components | 2-3 | 3-5 |
| Phase 3: Single Convert | Convert page, form, mutation, download | 3-4 | 6-9 |
| Phase 4: Batch Convert | Batch page, polling, progress, ZIP download | 3-4 | 9-13 |
| Phase 5: UI Polish | Layout, tabs, skeletons, responsive | 2-3 | 11-16 |
| Phase 6: Deployment | Environment, docs, build testing | 1-2 | 12-18 |
| Phase 7: Testing | All testing, bug fixes, refinement | 2-3 | 14-21 |

### Milestone Schedule (assuming 7 hours/day)

- **Day 1 Morning**: Phases 1-2 (Setup + Infrastructure)
- **Day 1 Afternoon**: Phase 3 (Single Convert Feature)
- **Day 2 Morning**: Phase 4 (Batch Convert Feature)
- **Day 2 Afternoon**: Phase 5 (UI Polish)
- **Day 3 Morning**: Phase 6 (Deployment Setup)
- **Day 3 Afternoon**: Phase 7 (Testing & Refinement)

### Critical Path
1. Phase 1 (Setup) → Phase 2 (Infrastructure) → Phase 3 (Single Convert)
2. Phase 2 (Infrastructure) → Phase 4 (Batch Convert)
3. All phases → Phase 7 (Testing)

---

## Appendix

### Key Design Decisions

1. **Vite over Create React App**
   - Faster build times
   - Better dev experience
   - Modern tooling
   - User preference

2. **Synchronous API for single files**
   - Simpler implementation
   - Immediate feedback
   - Better UX for small files
   - Backend already supports both modes

3. **Batch uses async API**
   - Required for multiple files
   - Better backend resource management
   - Progress tracking capability

4. **TanStack Query over Redux**
   - Better for API state
   - Built-in caching and refetching
   - Less boilerplate
   - Automatic polling support

5. **Shadcn over Material-UI**
   - Copy-paste components (not npm package)
   - Full customization
   - Tailwind CSS integration
   - Modern design system
   - User preference

### References
- [Shadcn/ui Documentation](https://ui.shadcn.com)
- [TanStack Query Documentation](https://tanstack.com/query/latest)
- [React Hook Form Documentation](https://react-hook-form.com)
- [Vite Documentation](https://vitejs.dev)
- [Tailwind CSS Documentation](https://tailwindcss.com)

---

**Plan Status**: Ready for Implementation
**Next Steps**: Review plan → Approve → Begin Phase 1 execution
