import { MhclgLogo } from '@/components/icons/mhclg-logo'
import Link from 'next/link'

const links = {
  '/acceptable-use-policy': 'Acceptable use policy',
  '/privacy-council-employees': 'Privacy (council employees)',
  '/privacy-members-public': 'Privacy (members of the public)',
}

export default function GovFooter() {
  return (
    <footer className="govuk-footer" role="contentinfo">
      <div className="govuk-width-container">
        <div className="govuk-!-padding-top-6">
          <MhclgLogo />
        </div>
        <div className="govuk-footer__meta">
          <div className="govuk-footer__meta-item govuk-footer__meta-item--grow">
            <h2 className="govuk-visually-hidden">Support links</h2>
            <ul className="govuk-footer__inline-list">
              {Object.entries(links).map(([key, value]) => (
                <li key={key} className="govuk-footer__inline-list-item">
                  <Link className="govuk-footer__link" href={key}>
                    {value}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
          <div className="govuk-footer__meta-item">
            <a
              className="govuk-footer__link govuk-footer__copyright-logo"
              href="https://www.nationalarchives.gov.uk/information-management/re-using-public-sector-information/uk-government-licensing-framework/crown-copyright/"
            >
              © Crown copyright
            </a>
          </div>
        </div>
      </div>
    </footer>
  )
}
