import Footer from '@/components/layout/footer'
import { GovukInit } from '@/components/layout/govuk-init'
import { Header } from '@/components/layout/header'
import { LegacyNav } from '@/components/layout/legacy-nav'
import { PhaseBanner } from '@/components/layout/phase-banner'
import { LockNavigationProvider } from '@/hooks/use-lock-navigation-context'
import { TanstackQueryProvider } from '@/providers/TanstackQueryProvider'
import PosthogProvider from '@/providers/posthog'
import { RecordingDbProvider } from '@/providers/transcription-db-provider'
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import { Toaster } from 'sonner'
import './globals.css'
import './govuk.scss'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Local Transcribe',
  description: 'Summaries and transcriptions',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" className={`govuk-template ${inter.className}`}>
      <body className="govuk-template__body">
        <a
          href="#main-content"
          className="govuk-skip-link"
          data-module="govuk-skip-link"
        >
          Skip to main content
        </a>

        <TanstackQueryProvider>
          <PosthogProvider>
            <LockNavigationProvider>
              <RecordingDbProvider>
                <Header />
                <div className="govuk-width-container">
                  <PhaseBanner />
                </div>
                <LegacyNav />

                <div className="govuk-width-container">
                  <main
                    id="main-content"
                    className="govuk-main-wrapper"
                    tabIndex={-1}
                  >
                    {children}
                  </main>
                </div>

                <Footer />
                <Toaster />
                <GovukInit />
              </RecordingDbProvider>
            </LockNavigationProvider>
          </PosthogProvider>
        </TanstackQueryProvider>
      </body>
    </html>
  )
}
