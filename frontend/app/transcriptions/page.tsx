import { PaginatedLabelledTranscriptions } from '@/components/recent-meetings/paginated-labelled-transcriptions'
import { Loader2 } from 'lucide-react'
import { Suspense } from 'react'
import { OfflineRecordings } from '@/components/recent-meetings/offline-recordings'
import { RecordingsSort } from '@/components/recent-meetings/recordings-sort'
import { UnlabelledTranscriptions } from '@/components/recent-meetings/unlabelled-transcriptions'
import { BannerNotification } from '@/components/banner-notification'
import { SearchRecordings } from '@/components/recent-meetings/search-recordings'
import { OFFLINE_RECORDINGS_ENABLED } from '@/lib/constants'

export default function TranscriptionsPage() {
  return (
    <div className="mx-auto max-w-3xl">
      <BannerNotification />
      <Suspense
        fallback={
          <div className="flex w-full items-center justify-center">
            <Loader2 className="animate-spin" />
          </div>
        }
      >
        {OFFLINE_RECORDINGS_ENABLED && <OfflineRecordings />}
        <RecordingsSort />
        <SearchRecordings />
        <UnlabelledTranscriptions />
        <PaginatedLabelledTranscriptions />
      </Suspense>
    </div>
  )
}
