import { GovukButtonLink } from '@/components/govuk'

export default function OfflinePage() {
  return (
    <div className="govuk-grid-row flex justify-center">
      <div className="govuk-grid-column-three-quarters">
        <h1 className="govuk-heading-l">Service Worker Fallback</h1>
        <p className="govuk-body">
          You need to be online to use this application. Please check your
          internet connection and try again.
        </p>
        <GovukButtonLink href="/" className="govuk-!-margin-top-4">
          Go back to homepage
        </GovukButtonLink>
      </div>
    </div>
  )
}
