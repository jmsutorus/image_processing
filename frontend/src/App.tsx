import { ConvertPage } from '@/features/convert'
import { Toaster } from 'sonner'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Header, Footer } from '@/components/Layout'

function App() {
  return (
    <div className="flex flex-col min-h-screen">
      <Header />

      <main className="flex-1 bg-background py-4 sm:py-6 md:py-8 px-3 sm:px-4">
        <div className="max-w-6xl mx-auto space-y-4 sm:space-y-6">
          {/* App Description */}
          <Card>
            <CardHeader className="p-4 sm:p-6">
              <CardTitle className="text-lg sm:text-xl">Image Conversion Service</CardTitle>
              <CardDescription className="text-xs sm:text-sm">
                Convert HEIC, DNG, JPEG, PNG, and WebP images to JPEG or WebP format with metadata preservation
              </CardDescription>
            </CardHeader>
          </Card>

          <ConvertPage />
        </div>
      </main>

      <Footer />
      <Toaster
        position="bottom-right"
        toastOptions={{
          classNames: {
            toast: 'group toast',
            title: 'text-sm font-semibold',
            description: 'text-sm opacity-90',
            actionButton: 'group-[.toast]:bg-primary group-[.toast]:text-primary-foreground',
            cancelButton: 'group-[.toast]:bg-muted group-[.toast]:text-muted-foreground',
          },
        }}
        richColors
      />
    </div>
  )
}

export default App
