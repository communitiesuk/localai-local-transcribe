'use client'
import { GovukAccordion } from '@/components/govuk/accordion'
import {
  GovukPanel,
  GovukPanelHeader,
  GovukPanelTitle,
  GovukPanelDescription,
  GovukPanelContent,
} from '@/components/govuk/panel'

export default function SupportPage() {
  return (
    <div className="govuk-width-container app-width-container--narrow">
      <div className="govuk-!-padding-top-6">
        <h1 className="govuk-heading-xl">Support Center</h1>

        <div className="govuk-grid-row govuk-!-margin-bottom-6">
          <div className="govuk-grid-column-one-half">
            <GovukPanel padding={4} border>
              <GovukPanelHeader>
                <GovukPanelTitle>Need Help?</GovukPanelTitle>
                <GovukPanelDescription>
                  Contact our support team
                </GovukPanelDescription>
              </GovukPanelHeader>
              <GovukPanelContent>
                <p className="govuk-hint">
                  Email us at:{' '}
                  <a
                    className="govuk-link"
                    href="mailto:minute-support@cabinetoffice.gov.uk"
                  >
                    minute-support@cabinetoffice.gov.uk
                  </a>
                </p>
              </GovukPanelContent>
            </GovukPanel>
          </div>

          <div className="govuk-grid-column-one-half">
            <GovukPanel padding={4} border>
              <GovukPanelHeader>
                <GovukPanelTitle>Response Time</GovukPanelTitle>
                <GovukPanelDescription>What to expect</GovukPanelDescription>
              </GovukPanelHeader>
              <GovukPanelContent>
                <p className="govuk-hint">
                  We aim to respond to all inquiries within 24 hours.
                </p>
              </GovukPanelContent>
            </GovukPanel>
          </div>
        </div>

        <div className="govuk-grid-row">
          <div className="govuk-grid-column-full">
            <GovukAccordion id="support-faq">
              <GovukAccordion.Section heading="How do I start a new transcription?">
                <p className="govuk-body">
                  Upload your audio or video file, or start a new recording
                  directly from your browser.
                </p>
              </GovukAccordion.Section>

              <GovukAccordion.Section heading="What file formats are supported?">
                <p className="govuk-body">
                  We support most common audio and video formats including MP3,
                  WAV, MP4, and M4A.
                </p>
              </GovukAccordion.Section>
            </GovukAccordion>
          </div>
        </div>
      </div>
    </div>
  )
}
