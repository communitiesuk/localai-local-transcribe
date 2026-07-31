import { PaginatedLabelledTranscriptions } from '@/components/recent-meetings/paginated-labelled-transcriptions'
import { Loader2 } from 'lucide-react'
import { Suspense } from 'react'
import { RecordingsSort } from '@/components/recent-meetings/recordings-sort'
import { UnlabelledTranscriptions } from '@/components/recent-meetings/unlabelled-transcriptions'

export default function TranscriptionsPage() {
  return (
    <div className="mx-auto max-w-3xl">
      <Suspense
        fallback={
          <div className="flex w-full items-center justify-center">
            <Loader2 className="animate-spin" />
          </div>
        }
      >
        <RecordingsSort />
        <UnlabelledTranscriptions />
        <PaginatedLabelledTranscriptions />
      </Suspense>
    </div>
  )
}
