import Link from 'next/link'
import GovFooter from '@/components/layout/footer'

export default function LogoutPage() {
  return (
    <>
      <div className="govuk-width-container py-12">
        <main className="govuk-main-wrapper" id="main-content" role="main">
          <div className="govuk-grid-row flex justify-center">
            <div className="govuk-grid-column-two-thirds">
              <h2 className="govuk-heading-m text-[var(--govuk-brand-colour)]">
                You have been signed out
              </h2>
              <p className="govuk-body">
                To sign back in please follow this{' '}
                <Link href="/" className="govuk-link">
                  link
                </Link>
                .
              </p>
            </div>
          </div>
        </main>
      </div>
      <GovFooter />
    </>
  )
}
