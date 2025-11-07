# Core Architecture

## Frameworks
- NextJS
- Tailwind css
- Shadcn

## Content Management
- **Post metadata**: Parsed using `gray-matter` (title, excerpt, date, author, coverImage, ogImage)
- **Markdown rendering**: Uses `remark` and `remark-html` to convert Markdown to HTML strings
- **Post API**: Core functions in `src/lib/api.ts`:
  - `getPostSlugs()`: Returns all post filenames from `_posts` directory
  - `getPostBySlug(slug)`: Reads and parses a single post with metadata
  - `getAllPosts()`: Returns all posts sorted by date (descending)

## Routing & Pages
- **Homepage** (`src/app/page.tsx`): Displays hero post (most recent) and older posts
- **Individual posts** (`src/app/posts/[slug]/page.tsx`): Dynamic routes using `generateStaticParams()`
- **Static generation**: All posts pre-rendered at build time using Next.js Static Generation

## Component Structure
Components in `src/app/_components/`:
- Presentational components for layout (Container, Header, Footer, Intro)
- Post-specific components (PostHeader, PostBody, PostTitle, CoverImage, DateFormatter)
- Home page components (HeroPost, MoreStories, PostPreview)
- Utility components (Avatar, Alert, SectionSeparator)

## TypeScript Interfaces
- `Post` interface in `src/interfaces/post.ts`: Defines post structure
- Path alias `@/*` maps to `./src/*` (configured in tsconfig.json)

# Commands

## Development
- `npm run dev`: Start development server with Turbopack
- `npm run build`: Build production bundle
- `npm start`: Start production server

## Type Checking
- TypeScript strict mode enabled in tsconfig.json
- Run `npx tsc --noEmit` to type check without building

# Code Style
- Use ES modules (import/export) syntax, not CommonJS (require)
- Destructure imports when possible (e.g., `import { foo } from 'bar'`)