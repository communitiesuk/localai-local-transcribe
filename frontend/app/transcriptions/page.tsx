import { PaginatedLabelledTranscriptions } from '@/components/recent-meetings/paginated-labelled-transcriptions'
import { Loader2 } from 'lucide-react'
import { Suspense } from 'react'
import { GovukAccordion } from '../../components/govuk/accordion'
import { GovukAccordionSection } from '../../components/govuk/accordion'
import { OfflineRecordings } from '@/components/recent-meetings/offline-recordings'
import { RecordingsSort } from '@/components/recent-meetings/recordings-sort'
import { UnlabelledTranscriptions } from '@/components/recent-meetings/unlabelled-transcriptions'
import { BannerNotification } from '@/components/banner-notification'

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
        <OfflineRecordings />
        <RecordingsSort />
        <UnlabelledTranscriptions />
        <PaginatedLabelledTranscriptions />
      </Suspense>
    </div>
  )
}
