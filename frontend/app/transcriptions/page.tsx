import { PaginatedLabelledTranscriptions } from '@/components/recent-meetings/paginated-labelled-transcriptions'
import { Loader2 } from 'lucide-react'
import { Suspense } from 'react'
import { GovukAccordion } from '../../components/govuk/accordion'
import { GovukAccordionSection } from '../../components/govuk/accordion'
import { OfflineRecordings } from '@/components/recent-meetings/offline-recordings'
import { UnlabelledTranscriptions } from '@/components/recent-meetings/unlabelled-transcriptions'

export default function TranscriptionsPage() {

  console.log('GovukAccordion:', GovukAccordion)
  console.log('GovukAccordion.Section:', GovukAccordionSection)
  return (

    <div className="mx-auto max-w-full">
      <h1 className="govuk-heading-l">My recordings</h1>
      <hr className="govuk-section-break govuk-section-break--m govuk-section-break--visible" />
      <h1 className="govuk-heading-s">Search</h1>
      <GovukAccordion id="search-my-recordings">
        <GovukAccordionSection heading="">
          <span>hello world</span>


        </GovukAccordionSection>
      </GovukAccordion>


      <Suspense
        fallback={
          <div className="flex w-full items-center justify-center">
            <Loader2 className="animate-spin" />
          </div>
        }
      >
        <OfflineRecordings />
        <UnlabelledTranscriptions />
        <PaginatedLabelledTranscriptions />
      </Suspense>
    </div>
  )
}
