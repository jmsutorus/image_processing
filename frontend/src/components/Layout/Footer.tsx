import { Heart } from 'lucide-react';

export function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="w-full border-t bg-background mt-auto">
      <div className="max-w-6xl mx-auto px-3 sm:px-4 py-4 sm:py-6">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 sm:gap-4">
          <div className="flex items-center gap-1 text-xs sm:text-sm text-muted-foreground">
            <span>&copy; {currentYear} Image Converter.</span>
            <span className="hidden sm:inline">Built with</span>
            <Heart className="h-3 w-3 fill-red-500 text-red-500" />
            <span className="hidden sm:inline">using React & FastAPI</span>
          </div>
          <div className="flex items-center gap-3 sm:gap-4 text-xs sm:text-sm text-muted-foreground">
            <a
              href="#"
              className="hover:text-foreground transition-colors"
            >
              Privacy
            </a>
            <a
              href="#"
              className="hover:text-foreground transition-colors"
            >
              Terms
            </a>
            <a
              href="#"
              className="hover:text-foreground transition-colors"
            >
              Contact
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
