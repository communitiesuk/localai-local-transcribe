'use client'

import { use, useEffect, useRef, useState } from 'react'
import { redirect, useRouter } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { LoaderCircle } from 'lucide-react'
import { BannerNotification } from '@/components/banner-notification'
import { GovukErrorSummary } from '@/components/govuk'
import type { ErrorItem } from '@/components/govuk/error-summary'
import { RecordingDetails } from '@/app/transcriptions/[transcriptionId]/RecordingDetails'
import {
  isTranscriptionProcessing,
  notifyRecordingSaved,
} from '@/app/transcriptions/[transcriptionId]/TranscriptionStatus'
import { getTranscriptionTranscriptionsTranscriptionIdGetOptions } from '@/lib/client/@tanstack/react-query.gen'
import { useBannerStore } from '@/stores/use-banner-store'

/**
 * Standalone "add details" step shown after starting a new recording or
 * upload. Reuses the same RecordingDetails form as the transcription page's
 * "Recording details" panel, but owns its own navigation: once details are
 * saved (or skipped), the user is redirected to the transcription (or home,
 * with a confirmation banner) once processing has finished.
 */
export default function AddRecordingMetadataPage(props: {
  params: Promise<{ transcriptionId: string }>
}) {
  const { transcriptionId } = use(props.params)
  const router = useRouter()
  const setBanner = useBannerStore((store) => store.setBanner)
  const [recordingDetailsErrors, setRecordingDetailsErrors] = useState<
    ErrorItem[]
  >([])
  const [isSaved, setIsSaved] = useState(false)
  const errorSummaryRef = useRef<HTMLDivElement | null>(null)

  const { data: transcription, isLoading } = useQuery({
    ...getTranscriptionTranscriptionsTranscriptionIdGetOptions({
      path: { transcription_id: transcriptionId },
    }),
    refetchInterval: (query) =>
      isSaved && isTranscriptionProcessing(query.state.data?.status)
        ? 2000
        : false,
    refetchOnWindowFocus: false,
  })

  useEffect(() => {
    if (!isSaved || !transcription) {
      return
    }
    if (isTranscriptionProcessing(transcription.status)) {
      return
    }
    notifyRecordingSaved(router, setBanner, transcription.id)
  }, [isSaved, transcription, router, setBanner])

  if (!transcription && !isLoading) {
    redirect('/')
  }

  if (isLoading) {
    return (
      <div className="flex h-72 flex-col items-center justify-center">
        <LoaderCircle size={80} className="animate-spin" aria-hidden="true" />
      </div>
    )
  }

  if (!transcription) {
    return null
  }

  if (isSaved) {
    return (
      <div className="flex h-72 flex-col items-center justify-center gap-4">
        <LoaderCircle size={80} className="animate-spin" aria-hidden="true" />
        <p className="govuk-body">Processing recording...</p>
      </div>
    )
  }

  const dateString =
    transcription.date_of_recording ?? transcription.created_datetime
  const date = new Date(dateString)
  const dateTimeLabel = `${date.toLocaleDateString('en-GB')} at ${date.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })}`

  return (
    <div className="govuk-grid-row">
      <div className="govuk-grid-column-two-thirds">
        <BannerNotification />
        {recordingDetailsErrors.length > 0 && (
          <GovukErrorSummary
            ref={errorSummaryRef}
            errorList={recordingDetailsErrors}
          />
        )}
        <RecordingDetails
          mode="standalone"
          dateTimeLabel={dateTimeLabel}
          transcription={transcription}
          onErrorListChange={setRecordingDetailsErrors}
          onStandaloneComplete={() => setIsSaved(true)}
        />
      </div>
    </div>
  )
}
