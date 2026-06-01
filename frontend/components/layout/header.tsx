import { MhclgLogo } from '@/components/icons/mhclg-logo'
import { API_PROXY_PATH } from '@/lib/constants'
import Link from 'next/link'

export function Header() {
  return (
    <header className="govuk-header" data-module="govuk-header">
      <div className="govuk-header__container govuk-width-container">
        <div className="govuk-header__logo">
          <Link
            href="/"
            className="govuk-header__link govuk-header__link--homepage"
          >
            <span className="govuk-header__logotype">
              <MhclgLogo className="govuk-header__logotype-crown" />
              <span className="govuk-header__product-name">
                Local Transcribe
              </span>
            </span>
          </Link>
        </div>
        <div className="govuk-header__content">
          <nav aria-label="Account" className="govuk-header__navigation">
            <ul className="govuk-header__navigation-list">
              <li className="govuk-header__navigation-item">
                <a
                  className="govuk-header__link"
                  href={`${API_PROXY_PATH}/signout`}
                >
                  Sign out
                </a>
              </li>
            </ul>
          </nav>
        </div>
      </div>
    </header>
  )
}
