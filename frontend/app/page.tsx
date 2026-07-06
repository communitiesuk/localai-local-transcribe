import { PosthogBanner } from '@/components/posthog-banner'
import { PaginatedTranscriptions } from '@/components/recent-meetings/paginated-transcriptions'
import { Loader2, Plus } from 'lucide-react'
import { GovukButtonLink } from '@/components/govuk'
import { Suspense } from 'react'

export default function Home() {
  return (
    <div className="govuk-grid-row flex justify-center">
      <PosthogBanner />
      <div className="govuk-grid-column-three-quarters">
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

        <Suspense
          fallback={
            <div className="govuk-body flex items-center gap-2">
              <Loader2 className="animate-spin" />
            </div>
          }
        >
          <PaginatedTranscriptions />
        </Suspense>
      </div>
    </div>
  )
}
