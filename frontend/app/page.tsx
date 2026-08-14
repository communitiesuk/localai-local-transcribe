import { PosthogBanner } from '@/components/posthog-banner'
import { PaginatedLabelledTranscriptions } from '@/components/recent-meetings/paginated-labelled-transcriptions'
import { Loader2, Plus } from 'lucide-react'
import { GovukButtonLink } from '@/components/govuk'
import { Suspense } from 'react'
import { BannerNotification } from '@/components/banner-notification'

export default function Home() {
  return (
    <div className="govuk-grid-row flex justify-center">
      <PosthogBanner />
      <div className="govuk-grid-column-three-quarters">
        <BannerNotification />
        <h1 className="govuk-heading-l govuk-!-margin-bottom-3">
          AI transcription and drafting service
        </h1>
        <p className="govuk-body govuk-hint">
          Transcribe and summarise your meetings with AI. Click the New Meeting
          button below to begin. Suitable up to{' '}
          <span className="font-bold">OFFICIAL SENSITIVE</span>.
        </p>

        <GovukButtonLink href="/new" variant="primary">
          <Plus />
          <span className="font-semibold">New meeting</span>
        </GovukButtonLink>
      </div>
    </div>
  )
}
