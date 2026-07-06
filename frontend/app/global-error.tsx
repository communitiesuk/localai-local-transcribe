'use client'

import * as Sentry from '@sentry/nextjs'
import { useEffect } from 'react'
import './globals.css'
import './govuk.scss'

// `global-error.tsx` renders when the root layout itself throws, so the
// layout chrome (header, footer, providers) is not available. We inline the
// minimum GOV.UK page shell here and import the styles directly, since the
// layout's style imports will not have run.
export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    Sentry.captureException(error)
  }, [error])

  return (
    <html lang="en" className="govuk-template">
      <body className="govuk-template__body">
        <div className="govuk-width-container">
          <main className="govuk-main-wrapper" id="main-content">
            <div className="govuk-grid-row">
              <div className="govuk-grid-column-two-thirds">
                <h1 className="govuk-heading-l">
                  Sorry, there is a problem with the service
                </h1>
                <p className="govuk-body">Try again later.</p>
                <button
                  type="button"
                  className="govuk-button"
                  data-module="govuk-button"
                  onClick={() => reset()}
                >
                  Try again
                </button>
              </div>
            </div>
          </main>
        </div>
      </body>
    </html>
  )
}
