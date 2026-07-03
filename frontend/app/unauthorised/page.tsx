import React from 'react'
import {
  GovukPanel,
  GovukPanelHeader,
  GovukPanelTitle,
  GovukPanelContent,
} from '@/components/govuk/panel'

function Unauthorised(): React.JSX.Element {
  return (
    <div
      className="govuk-!-padding-top-9"
      style={{ minHeight: '100vh', backgroundColor: '#f9fafb' }}
    >
      <div className="govuk-width-container">
        <div className="govuk-grid-row flex justify-center">
          <div className="govuk-grid-column-two-third govuk-grid-column-one-third govuk-!-margin-0-auto">
            <GovukPanel padding={6} border>
              <GovukPanelHeader>
                <GovukPanelTitle className="govuk-heading-m govuk-!-text-align-centre">
                  Unauthorised Access
                </GovukPanelTitle>
              </GovukPanelHeader>
              <GovukPanelContent>
                <p className="govuk-body govuk-!-text-align-centre">
                  Sorry, you don&apos;t have permission to access this page.
                  Please contact your administrator if you believe this is an
                  error.
                </p>
              </GovukPanelContent>
            </GovukPanel>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Unauthorised
