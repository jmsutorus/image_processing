# Deployment Guide

This guide covers deploying the Image Conversion Service frontend to production.

## Pre-Deployment Checklist

- [ ] Backend API is deployed and accessible
- [ ] Backend CORS is configured for production frontend URL
- [ ] Environment variables are documented
- [ ] Production build succeeds locally
- [ ] All features tested and working

## Backend CORS Configuration for Production

Before deploying the frontend, you **must** update the backend CORS configuration to allow requests from your production domain.

### Step 1: Update Backend CORS

Edit `backend/app.py` and add your production frontend URL to the CORS allowed origins:

```python
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Image Processing API",
    description="Convert HEIC, DNG, and JPEG images to JPEG or WebP format",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",           # Local development
        "http://localhost:3000",           # Alternative local port
        "https://yourapp.vercel.app",      # Production Vercel URL
        "https://yourapp.netlify.app",     # Production Netlify URL
        # Add your custom domain if applicable
        "https://yourdomain.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)
```

### Step 2: Rebuild Backend Docker Container

After updating CORS, you **must** rebuild the Docker container:

```bash
# Navigate to project root
cd ../

# Rebuild and restart the backend container
docker-compose build app
docker-compose up -d app

# Verify the container is running
docker-compose ps
```

### Step 3: Test CORS

Test that CORS is working correctly:

```bash
# Replace with your production frontend URL
curl -X OPTIONS http://your-backend-url:8000/convert-to-webp \
  -H "Origin: https://yourapp.vercel.app" \
  -H "Access-Control-Request-Method: POST" \
  -i

# Expected response should include:
# HTTP/1.1 200 OK
# access-control-allow-origin: https://yourapp.vercel.app
# access-control-allow-methods: DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT
```

## Deployment Options

### Option 1: Vercel (Recommended)

Vercel offers seamless deployment with automatic builds, environment variables, and edge CDN.

#### Deploy via Vercel CLI

1. **Install Vercel CLI:**
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel:**
   ```bash
   vercel login
   ```

3. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

4. **Deploy:**
   ```bash
   vercel
   ```

   Follow the prompts:
   - Set up and deploy: `Y`
   - Scope: Choose your account
   - Link to existing project: `N`
   - Project name: `image-converter` (or your choice)
   - Directory: `./` (current directory)
   - Override settings: `N`

5. **Configure Environment Variables:**

   Option A: Via CLI
   ```bash
   vercel env add VITE_API_URL production
   # Enter: https://your-backend-api-url.com
   ```

   Option B: Via Dashboard
   - Go to your Vercel project dashboard
   - Navigate to Settings → Environment Variables
   - Add variable:
     - Name: `VITE_API_URL`
     - Value: `https://your-backend-api-url.com`
     - Environment: Production

6. **Redeploy to apply environment variables:**
   ```bash
   vercel --prod
   ```

7. **Get your deployment URL:**
   - Vercel will provide a URL like `https://yourapp.vercel.app`
   - Add this URL to backend CORS (see Backend CORS Configuration above)

#### Deploy via Vercel GitHub Integration

1. Push your code to GitHub
2. Go to [vercel.com](https://vercel.com) and sign in
3. Click "New Project"
4. Import your GitHub repository
5. Configure:
   - **Framework Preset:** Vite
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
6. Add environment variable `VITE_API_URL` with your backend URL
7. Click "Deploy"

### Option 2: Netlify

Netlify is another excellent option with similar features to Vercel.

#### Deploy via Netlify CLI

1. **Install Netlify CLI:**
   ```bash
   npm install -g netlify-cli
   ```

2. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

3. **Build the project:**
   ```bash
   npm run build
   ```

4. **Deploy:**
   ```bash
   netlify deploy --prod
   ```

   Follow the prompts:
   - Authorize Netlify CLI
   - Create & configure a new site: `Y`
   - Team: Choose your team
   - Site name: `image-converter` (or your choice)
   - Publish directory: `dist`

5. **Configure Environment Variables:**

   Option A: Via CLI
   ```bash
   netlify env:set VITE_API_URL https://your-backend-api-url.com
   ```

   Option B: Via Dashboard
   - Go to your Netlify site dashboard
   - Navigate to Site settings → Environment variables
   - Add variable:
     - Key: `VITE_API_URL`
     - Value: `https://your-backend-api-url.com`

6. **Redeploy:**
   ```bash
   netlify deploy --prod
   ```

#### Deploy via Netlify GitHub Integration

1. Push your code to GitHub
2. Go to [netlify.com](https://netlify.com) and sign in
3. Click "Add new site" → "Import an existing project"
4. Choose GitHub and select your repository
5. Configure:
   - **Base directory:** `frontend`
   - **Build command:** `npm run build`
   - **Publish directory:** `frontend/dist`
6. Add environment variable `VITE_API_URL` with your backend URL
7. Click "Deploy site"

### Option 3: Other Platforms

#### Cloudflare Pages

```bash
# Build locally
cd frontend
npm run build

# Deploy via Cloudflare Pages dashboard
# Upload the dist/ folder
# Configure SPA routing to serve index.html for all routes
```

#### GitHub Pages

Not recommended for this project due to:
- Requires backend proxy or CORS
- No native environment variable support
- Limited build process integration

#### AWS S3 + CloudFront

1. Build the project: `npm run build`
2. Upload `dist/` contents to S3 bucket
3. Configure CloudFront distribution
4. Set up SPA routing (redirect all 404s to index.html)
5. Configure environment variables via build process or replace at build time

## Post-Deployment Verification

After deploying, verify everything works:

### 1. Test Core Functionality

- [ ] Visit your deployed URL
- [ ] Upload a single image (HEIC, DNG, or JPEG)
- [ ] Verify conversion works and file downloads
- [ ] Test batch upload (multiple files)
- [ ] Verify batch download (ZIP file)
- [ ] Test on mobile device

### 2. Check Network Requests

Open browser DevTools (F12) → Network tab:

- [ ] API requests go to correct backend URL
- [ ] No CORS errors in console
- [ ] All requests return 200 OK (or appropriate status)
- [ ] File uploads complete successfully

### 3. Test Error Scenarios

- [ ] Test with oversized file (> 200MB)
- [ ] Test with unsupported file type
- [ ] Test with backend offline (should show error message)

### 4. Performance Check

Use Lighthouse (in Chrome DevTools):

- [ ] Performance score > 85
- [ ] Accessibility score > 90
- [ ] Best Practices score > 85
- [ ] SEO score > 80

### 5. Browser Compatibility

Test in multiple browsers:

- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)
- [ ] Mobile Safari (iOS)
- [ ] Chrome Mobile (Android)

## Environment Variables Reference

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API base URL | `https://api.yourdomain.com` |

### Setting Environment Variables

**Vercel:**
```bash
vercel env add VITE_API_URL production
```

**Netlify:**
```bash
netlify env:set VITE_API_URL https://api.yourdomain.com
```

**Via Platform Dashboard:**
- Vercel: Project Settings → Environment Variables
- Netlify: Site Settings → Environment variables

## Troubleshooting Production Issues

### Issue: CORS Errors in Production

**Symptoms:**
- Console errors: "Access to XMLHttpRequest has been blocked by CORS policy"
- Network requests fail with CORS error

**Solution:**
1. Verify production frontend URL is in backend `allow_origins`
2. Rebuild backend Docker container: `docker-compose build app && docker-compose up -d app`
3. Clear browser cache
4. Test CORS with curl (see Backend CORS Configuration above)

### Issue: Environment Variables Not Applied

**Symptoms:**
- API requests go to wrong URL
- Features not working as expected

**Solution:**
1. Verify environment variable is set on platform (Vercel/Netlify dashboard)
2. Variable name must start with `VITE_`
3. Redeploy after adding/changing environment variables
4. Check build logs for environment variable values (they should be visible)

### Issue: 404 on Page Refresh

**Symptoms:**
- Refreshing page shows 404 error
- Direct URL access fails

**Solution:**
1. Verify SPA routing configuration:
   - Vercel: Check `vercel.json` has rewrites
   - Netlify: Check `netlify.toml` has redirects
2. Redeploy with correct configuration files

### Issue: Build Fails on Platform

**Symptoms:**
- Deployment fails during build step
- Build logs show errors

**Solution:**
1. Test build locally: `npm run build`
2. Fix any TypeScript errors
3. Ensure all dependencies are in `package.json` (not just devDependencies)
4. Check Node.js version matches local (18+)
5. Review platform build logs for specific errors

### Issue: Slow Initial Load

**Symptoms:**
- First page load takes > 5 seconds
- Large bundle sizes

**Solution:**
1. Check bundle analyzer: `npm run build` (look at sizes)
2. Verify code splitting is working (check `dist/assets/`)
3. Enable CDN/edge caching on platform
4. Optimize images in `public/` folder
5. Consider lazy loading routes

## Rollback Procedure

If deployment has issues:

**Vercel:**
```bash
# List deployments
vercel ls

# Promote a previous deployment to production
vercel promote <deployment-url>
```

**Netlify:**
```bash
# Via dashboard: Deploys → Click on previous deploy → Publish deploy
```

## Monitoring & Analytics

### Recommended Tools

1. **Error Tracking:** Sentry, LogRocket, or Rollbar
2. **Analytics:** Google Analytics, Plausible, or Vercel Analytics
3. **Performance Monitoring:** Vercel Analytics or Lighthouse CI
4. **Uptime Monitoring:** UptimeRobot, Pingdom, or Better Uptime

### Setting up Sentry (Optional)

```bash
npm install @sentry/react
```

```typescript
// src/main.tsx
import * as Sentry from '@sentry/react';

Sentry.init({
  dsn: "your-sentry-dsn",
  environment: import.meta.env.MODE,
  tracesSampleRate: 1.0,
});
```

## Security Considerations

### Production Best Practices

- [ ] Use HTTPS for both frontend and backend
- [ ] Set secure CORS origins (no wildcards in production)
- [ ] Enable CSP headers if applicable
- [ ] Keep dependencies updated
- [ ] Don't expose API keys in frontend code
- [ ] Use environment variables for all configuration
- [ ] Enable rate limiting on backend
- [ ] Monitor for security vulnerabilities

### Content Security Policy (Optional)

Add to `vercel.json` or `netlify.toml`:

```json
{
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "Content-Security-Policy",
          "value": "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self' https://your-api-url.com"
        }
      ]
    }
  ]
}
```

## Continuous Deployment

### Automatic Deployment with Git

Both Vercel and Netlify support automatic deployments:

1. **Connect Repository:**
   - Link your GitHub/GitLab repository to platform

2. **Configure Branch:**
   - Production branch: `main`
   - Preview branches: Feature branches get preview URLs

3. **Commit Triggers:**
   - Push to `main` → Automatic production deployment
   - Push to feature branch → Preview deployment

4. **Deployment Protection:**
   - Add deployment protection rules
   - Require manual approval for production
   - Run tests before deployment

## Custom Domain Setup

### Add Custom Domain

**Vercel:**
1. Go to Project Settings → Domains
2. Add your domain: `yourdomain.com`
3. Configure DNS records as instructed
4. Wait for SSL certificate provisioning

**Netlify:**
1. Go to Site Settings → Domain management
2. Add custom domain: `yourdomain.com`
3. Update DNS records at your registrar
4. SSL certificate automatically provisions

### DNS Configuration

Typically requires:
- **A Record:** Points to platform's IP address
- **CNAME Record:** Points `www` to platform's domain

Platform will provide specific DNS instructions.

## Support

For deployment issues:
- **Vercel:** [vercel.com/support](https://vercel.com/support)
- **Netlify:** [netlify.com/support](https://netlify.com/support)
- **Project Issues:** Open an issue on GitHub

---

**Last Updated:** 2025-11-07
