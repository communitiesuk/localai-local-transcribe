'use client'

import { GovukButton, GovukNotificationBanner } from '@/components/govuk'
import * as Sentry from '@sentry/nextjs'
import { useEffect } from 'react'

export default function Error({
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
    <div className="govuk-grid-row">
      <div className="govuk-grid-column-two-thirds">
        <h1 className="govuk-heading-l">
          Sorry, there is a problem with the service
        </h1>

        <GovukNotificationBanner
          title="There is a problem"
          className="govuk-!-margin-bottom-6"
        >
          <p className="govuk-notification-banner__heading">
            Something went wrong while loading this page.
          </p>
        </GovukNotificationBanner>

        <p className="govuk-body">Try again later.</p>

        <GovukButton
          type="button"
          onClick={() => reset()}
          className="govuk-!-margin-bottom-6"
        >
          Try again
        </GovukButton>

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
