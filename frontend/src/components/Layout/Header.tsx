import { Image } from 'lucide-react';

export function Header() {
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="max-w-6xl mx-auto px-3 sm:px-4 h-14 sm:h-16 flex items-center justify-between">
        <div className="flex items-center gap-2 sm:gap-3">
          <div className="flex items-center justify-center h-8 w-8 sm:h-10 sm:w-10 rounded-lg bg-primary/10">
            <Image className="h-4 w-4 sm:h-6 sm:w-6 text-primary" />
          </div>
          <div>
            <h1 className="text-base sm:text-lg font-semibold">Image Converter</h1>
            <p className="text-xs text-muted-foreground hidden sm:block">
              Fast, secure image conversion
            </p>
          </div>
        </div>
        <nav className="flex items-center gap-2 sm:gap-4">
          <a
            href="https://github.com"
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs sm:text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            GitHub
          </a>
          <a
            href="#"
            className="text-xs sm:text-sm text-muted-foreground hover:text-foreground transition-colors hidden sm:inline"
          >
            About
          </a>
        </nav>
      </div>
    </header>
  );
}
