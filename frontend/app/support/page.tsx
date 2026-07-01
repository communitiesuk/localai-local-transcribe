'use client'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { GovukAccordion } from '@/components/govuk/accordion'

export default function SupportPage() {
  return (
    <div className="container max-w-4xl py-6 md:py-10">
      <div className="space-y-6">
        <h1 className="text-4xl font-bold tracking-tight">Support Center</h1>

        <div className="grid gap-4 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Need Help?</CardTitle>
              <CardDescription>Contact our support team</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">
                Email us at:{' '}
                <a href="mailto:minute-support@cabinetoffice.gov.uk">
                  minute-support@cabinetoffice.gov.uk
                </a>
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Response Time</CardTitle>
              <CardDescription>What to expect</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">
                We aim to respond to all inquiries within 24 hours.
              </p>
            </CardContent>
          </Card>
        </div>

        <GovukAccordion id="support-faq" className="w-full">
          <GovukAccordion.Section heading="How do I start a new transcription?" _accordionId='new-transcription'>
            <p className='govuk-body'>
              Upload your audio or video file, or start a new recording directly
              from your browser.
            </p>
          </GovukAccordion.Section>

          <GovukAccordion.Section heading="What file formats are supported?" _accordionId='file-formats'>
            <p className='govuk-body'>
              We support most common audio and video formats including MP3, WAV,
              MP4, and M4A.
            </p>
          </GovukAccordion.Section>
        </GovukAccordion>
      </div>
    </div>
  )
}
