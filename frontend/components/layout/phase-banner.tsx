import { GovukTag } from '@/components/govuk'

export function PhaseBanner() {
  return (
    <div className="govuk-phase-banner">
      <p className="govuk-phase-banner__content">
        <GovukTag className="govuk-phase-banner__content__tag">Beta</GovukTag>
        <span className="govuk-phase-banner__text">
          This is a new service –{' '}
          <a
            className="govuk-link"
            href="mailto:LocalTranscribe@communities.gov.uk"
          >
            email us your feedback
          </a>{' '}
          to help us improve it.
        </span>
      </p>
    </div>
  )
}
