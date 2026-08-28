'use client'
import { use } from 'react'

import AudioPlayerComponent from '@/components/audio/audio-player'
import { StartTranscriptionSection } from '@/components/audio/start-transcription-section'
import { GovukHeading, GovukNotificationBanner } from '@/components/govuk'
import { useStartTranscription } from '@/hooks/useStartTranscription'
import {
  RecordingDbItem,
  useRecordingDb,
} from '@/providers/transcription-db-provider'
import { useQuery } from '@tanstack/react-query'
import { Loader2 } from 'lucide-react'
import { FormProvider } from 'react-hook-form'

export default function RecordingPage(props: {
  params: Promise<{ recordingId: string }>
}) {
  const params = use(props.params)

  const { recordingId } = params

  const { getRecording } = useRecordingDb()
  const {
    data: recording,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['db-recording-get', recordingId],
    queryFn: async () => await getRecording(recordingId),
  })
  if (isLoading) {
    return (
      <div className="govuk-grid-row">
        <div className="govuk-grid-column-two-thirds">
          <GovukHeading>Upload an offline recording</GovukHeading>
          <p className="govuk-body flex items-center gap-2">
            <Loader2 className="animate-spin" aria-hidden="true" /> Loading...
          </p>
        </div>
      </div>
    )
  }
  if (error || !recording) {
    return (
      <div className="govuk-grid-row">
        <div className="govuk-grid-column-two-thirds">
          <GovukHeading>Upload an offline recording</GovukHeading>
          <GovukNotificationBanner title="Recording not found">
            <p className="govuk-notification-banner__heading">
              Recording with id {recordingId} was not found.
            </p>
          </GovukNotificationBanner>
        </div>
      </div>
    )
  }
  return (
    <div className="govuk-grid-row">
      <div className="govuk-grid-column-two-thirds">
        <GovukHeading>Upload an offline recording</GovukHeading>
        <RecordingUploadForm recording={recording} />
      </div>
    </div>
  )
}

function RecordingUploadForm({ recording }: { recording: RecordingDbItem }) {
  const { form, isPending, onSubmit } = useStartTranscription({
    defaultValues: {
      file: recording.blob,
      recordingId: recording.recording_id,
    },
  })

  return (
    <FormProvider {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)}>
        <AudioPlayerComponent audioBlob={recording.blob} />
        <StartTranscriptionSection isPending={isPending} isShowing={true} />
      </form>
    </FormProvider>
  )
}
