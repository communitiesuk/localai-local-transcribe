import { PosthogBanner } from '@/components/posthog-banner'
import { PaginatedTranscriptions } from '@/components/recent-meetings/paginated-transcriptions'
import { Button } from '@/components/ui/button'
import { Loader2, Plus } from 'lucide-react'
import Link from 'next/link'
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
        <Button
          className="mb-6 w-full bg-blue-500 p-6 hover:bg-blue-800 active:bg-amber-400"
          asChild
        >
          <Link href="/new">
            <Plus />
            New meeting
          </Link>
        </Button>
        <GovukButtonLink
          href="/new"
          variant="primary"
          className="flex !h-auto !w-full !items-center !justify-center gap-2 !rounded-sm !border-0 !bg-blue-500 !p-0 !text-base !shadow-none hover:!bg-blue-800 active:!bg-amber-400"
        >
          <Plus />
          New meeting
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

// Todo: Fix button
