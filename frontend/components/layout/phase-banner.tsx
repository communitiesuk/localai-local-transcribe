import Link from 'next/link'

export function PhaseBanner() {
  return (
    <div className="govuk-phase-banner">
      <p className="govuk-phase-banner__content">
        <strong className="govuk-tag govuk-phase-banner__content__tag">
          Alpha
        </strong>
        <span className="govuk-phase-banner__text">
          This is a new service. Help us improve it and{' '}
          <Link
            className="govuk-link"
            href="https://surveys.publishing.service.gov.uk/s/MAQMR1/"
            target="_blank"
            rel="noopener noreferrer"
          >
            give your feedback
          </Link>
          .
        </span>
      </p>
    </div>
  )
}
