export default function SupportPage() {
  return (
    <div className="govuk-grid-row">
      <div className="govuk-grid-column-full">
        <h1 className="govuk-heading-xl govuk-!-margin-bottom-6">Support</h1>

        <p className="govuk-body-l govuk-!-margin-bottom-5">
          If you&apos;ve got a problem, or need support with using Local Transcribe,
          please email us:{' '}
          <a
            className="govuk-link"
            href="mailto:LocalTranscribeSupport@communities.gov.uk"
          >
            LocalTranscribeSupport@communities.gov.uk
          </a>
          .
        </p>

        <p className="govuk-body-l govuk-!-margin-bottom-0">
          Someone from the Local Transcribe team will respond within 5 working days.
        </p>
      </div>
    </div>
  )
}
