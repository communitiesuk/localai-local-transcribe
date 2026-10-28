import { GovukBody, GovukHeading } from '@/components/govuk'

export default function SupportPage() {
  return (
    <div className="govuk-grid-row">
      <div className="govuk-grid-column-full">
        <GovukHeading size="xl" className="govuk-!-margin-bottom-6">
          Support
        </GovukHeading>

        <GovukBody size="l" className="govuk-!-margin-bottom-5">
          If you&apos;ve got a problem, or need support with using Local
          Transcribe, please email us:{' '}
          <a
            className="govuk-link"
            href="mailto:LocalTranscribeSupport@communities.gov.uk"
          >
            LocalTranscribeSupport@communities.gov.uk
          </a>
          .
        </GovukBody>

        <GovukBody size="l" className="govuk-!-margin-bottom-0">
          Someone from the Local Transcribe team will respond within 5 working
          days.
        </GovukBody>
      </div>
    </div>
  )
}
