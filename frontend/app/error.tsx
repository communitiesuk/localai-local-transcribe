'use client'

import * as Sentry from '@sentry/nextjs'
import { useEffect } from 'react'

export default function Error({
  error,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    Sentry.captureException(error)
  }, [error])

  return (
    <div className="govuk-grid-row">
      <div className="govuk-grid-column-two-thirds">
        <h1 className="govuk-heading-l">
          Sorry, there is a problem with the service
        </h1>

        <p className="govuk-body">Try again later.</p>

        <p className="govuk-body">
          <a className="govuk-link" href="/support">
            Contact the Local Transcribe team
          </a>{' '}
          if the problem continues.
        </p>
      </div>
    </div>
  )
}
