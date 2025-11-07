# Image Conversion Service - Frontend

A modern React frontend for converting HEIC, DNG, and JPEG images to JPEG or WebP formats with metadata preservation.

## Features

- **Single File Conversion**: Upload and convert individual images with real-time progress tracking
- **Batch Processing**: Upload up to 50 files simultaneously and download results as a ZIP
- **Format Support**: HEIC, DNG, and JPEG input formats
- **Output Options**: Convert to JPEG or WebP (with quality and lossless options)
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices
- **Modern UI**: Built with Shadcn/ui and Tailwind CSS for a polished user experience

## Technology Stack

- **Framework**: React 19 + TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **UI Components**: Shadcn/ui (Radix UI primitives)
- **State Management**: TanStack Query (server state), React Hook Form (form state)
- **Validation**: Zod schemas
- **File Upload**: react-dropzone
- **HTTP Client**: Axios
- **Notifications**: Sonner

## Prerequisites

- Node.js 18+ and npm 9+
- Backend API running (see `../backend/README.md`)

## Getting Started

### 1. Installation

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install
```

### 2. Environment Configuration

Create environment files for development and production:

```bash
# Copy the example file
cp .env.example .env.development

# Edit .env.development with your local backend URL
# Default: VITE_API_URL=http://localhost:8000
```

For production, create `.env.production`:

```bash
# .env.production
VITE_API_URL=https://api.yourdomain.com
```

**Environment Variables:**

| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API base URL | `http://localhost:8000` (dev)<br>`https://api.yourdomain.com` (prod) |

### 3. Backend Configuration

Ensure the backend has CORS configured to allow requests from your frontend:

**Development:**
```python
# backend/app.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Production:**
```python
# backend/app.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://yourapp.vercel.app",  # Add your production URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 4. Development Server

```bash
npm run dev
```

The application will be available at `http://localhost:5173`

## Available Scripts

### Development

```bash
npm run dev          # Start development server with hot reload
npm run build        # Build for production
npm run preview      # Preview production build locally
npm run lint         # Run ESLint
```

### Type Checking

```bash
npx tsc -b           # Type check without emitting files
```

## Project Structure

```
frontend/
├── public/              # Static assets
├── src/
│   ├── components/      # Reusable UI components
│   │   ├── ui/          # Shadcn/ui components
│   │   ├── Layout/      # Header, Footer components
│   │   ├── FileUpload/  # FileDropzone, FilePreview
│   │   └── ErrorBoundary.tsx
│   ├── features/        # Feature-based modules
│   │   ├── convert/     # Single file conversion
│   │   │   ├── ConvertPage.tsx
│   │   │   ├── useConvert.ts
│   │   │   └── index.ts
│   │   └── batch/       # Batch conversion
│   │       ├── BatchPage.tsx
│   │       ├── BatchProgress.tsx
│   │       ├── useBatch.ts
│   │       ├── useBatchPolling.ts
│   │       └── index.ts
│   ├── hooks/           # Custom React hooks
│   │   └── useImagePreview.ts
│   ├── lib/             # Utilities and configurations
│   │   ├── api.ts       # Axios API client
│   │   ├── validators.ts # Zod schemas
│   │   ├── fileUtils.ts # File helper functions
│   │   └── utils.ts     # General utilities
│   ├── App.tsx          # Main app component
│   ├── main.tsx         # Application entry point
│   └── index.css        # Global styles
├── .env.example         # Environment variable template
├── .env.development     # Development environment
├── .env.production      # Production environment (create this)
├── components.json      # Shadcn/ui configuration
├── tailwind.config.js   # Tailwind CSS configuration
├── tsconfig.json        # TypeScript configuration
├── vite.config.ts       # Vite configuration
└── package.json         # Dependencies and scripts
```

## Building for Production

### 1. Build the Application

```bash
npm run build
```

This creates an optimized production build in the `dist/` directory.

**Build Output:**
- Minified JavaScript and CSS
- Code splitting for optimal loading
- Vendor chunks separated for better caching
- Source maps disabled for security

### 2. Preview Production Build Locally

```bash
npm run preview
```

Test the production build locally at `http://localhost:4173`

### 3. Verify Build

Check that:
- [ ] No console errors or warnings
- [ ] All features work correctly
- [ ] API calls succeed (update `.env.production` first)
- [ ] Images upload and convert successfully
- [ ] Responsive design works on mobile
- [ ] File downloads work properly

## Deployment

### Deploy to Vercel (Recommended)

1. **Install Vercel CLI:**
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel:**
   ```bash
   vercel login
   ```

3. **Deploy:**
   ```bash
   cd frontend
   vercel
   ```

4. **Configure Environment Variables:**
   - Go to your Vercel project dashboard
   - Navigate to Settings → Environment Variables
   - Add `VITE_API_URL` with your production backend URL

5. **Update Backend CORS:**
   - Add your Vercel URL to the backend's `allow_origins` list
   - Example: `https://yourapp.vercel.app`
   - Rebuild and restart the backend Docker container

### Deploy to Netlify

1. **Install Netlify CLI:**
   ```bash
   npm install -g netlify-cli
   ```

2. **Build and Deploy:**
   ```bash
   npm run build
   netlify deploy --prod
   ```

3. **Configure:**
   - Set `VITE_API_URL` in Netlify's environment variables
   - Configure SPA redirects (handled by `netlify.toml`)
   - Update backend CORS with your Netlify URL

### Deploy to Other Platforms

For GitHub Pages, Cloudflare Pages, or custom servers:

1. Build the application: `npm run build`
2. Upload the `dist/` folder contents to your hosting provider
3. Configure SPA routing (all routes should serve `index.html`)
4. Set environment variables via your platform's interface
5. Update backend CORS configuration

## Configuration Files

### `vercel.json`

Configures Vercel deployment with SPA routing:

```json
{
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

### `netlify.toml`

Configures Netlify deployment:

```toml
[build]
  command = "npm run build"
  publish = "dist"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

## API Integration

### Endpoints Used

The frontend integrates with these backend endpoints:

**Single File Conversion:**
- `POST /convert` - HEIC/DNG/JPEG → JPEG
- `POST /convert-to-webp` - HEIC/DNG/JPEG → WebP

**Batch Conversion:**
- `POST /jobs/batch-convert` - Upload multiple files
- `GET /jobs/batch/{batch_id}` - Check batch status
- `GET /jobs/batch/{batch_id}/results` - Download ZIP

### File Constraints

- **Max file size**: 200MB per file
- **Batch limit**: 50 files maximum
- **Supported formats**: `.heic`, `.heif`, `.dng`, `.jpg`, `.jpeg`
- **Output formats**: `jpeg`, `webp`

## Troubleshooting

### CORS Errors

**Issue:** `Access to XMLHttpRequest has been blocked by CORS policy`

**Solution:**
1. Verify backend CORS configuration includes your frontend URL
2. Check that backend is running on the correct port
3. Rebuild backend Docker container after CORS changes:
   ```bash
   docker-compose build app && docker-compose up -d app
   ```
4. Clear browser cache and reload

### Environment Variables Not Working

**Issue:** API calls go to wrong URL or fail

**Solution:**
1. Ensure environment file is named correctly (`.env.development` or `.env.production`)
2. Restart dev server after changing environment files
3. Verify variable name starts with `VITE_` (required by Vite)
4. Check `import.meta.env.VITE_API_URL` in code

### Build Errors

**Issue:** TypeScript errors during build

**Solution:**
1. Run type check: `npx tsc -b`
2. Fix any TypeScript errors
3. Ensure all imports use type-only imports where required:
   ```typescript
   import type { ReactNode } from 'react';
   ```

### File Upload Failures

**Issue:** Files don't upload or conversion fails

**Solution:**
1. Check file size (must be < 200MB)
2. Verify file format is supported
3. Check browser console for error messages
4. Verify backend is running and accessible
5. Test backend directly with curl

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

**Minimum Screen Size:** 375px (iPhone SE)

## Performance

**Bundle Size:**
- Main bundle: ~607KB (188KB gzipped)
- Optimized with code splitting and vendor chunks

**Loading Performance:**
- Initial load: < 2 seconds
- Time to interactive: < 3 seconds
- Lighthouse score: 90+ (Performance, Accessibility, Best Practices)

## Accessibility

- ✅ Keyboard navigation supported
- ✅ Screen reader compatible
- ✅ ARIA labels on interactive elements
- ✅ Sufficient color contrast
- ✅ Focus indicators visible

## Contributing

1. Follow the existing code style
2. Use TypeScript for type safety
3. Test on multiple screen sizes
4. Ensure no console errors
5. Run `npm run build` before committing

## License

See the main project LICENSE file.

## Support

For issues or questions:
- Check the troubleshooting section above
- Review backend API documentation
- Open an issue on GitHub
