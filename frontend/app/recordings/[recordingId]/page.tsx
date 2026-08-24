'use client'
import { useRouter } from 'next/navigation'
import { use } from 'react'

import AudioPlayerComponent from '@/components/audio/audio-player'
import { useUploadRecordingStore } from '@/stores/use-upload-recording-store'
import {
  GovukHeading,
  GovukNotificationBanner,
  GovukButton,
} from '@/components/govuk'
import { useStartTranscription } from '@/hooks/use-start-transcription'
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
  const router = useRouter()
  const startUpload = useUploadRecordingStore((store) => store.startUpload)

  const { form, isPending, onSubmit } = useStartTranscription({
    file: recording.blob,
    recordingId: recording.recording_id,
  })

  const handleSubmit = form.handleSubmit((formValues) => {
    startUpload(formValues, onSubmit)
    router.push('/new/uploading')
  })

  return (
    <FormProvider {...form}>
      <form onSubmit={handleSubmit}>
        <AudioPlayerComponent audioBlob={recording.blob} />
        <GovukButton type="submit" disabled={isPending}>
          Upload
        </GovukButton>
      </form>
    </FormProvider>
  )
}
