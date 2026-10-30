import { DownloadButton } from '@/components/download-button'
import { GovukNotificationBanner } from '@/components/govuk'
import { StatusBadge } from '@/components/status-icon'
import { TranscriptionTitleEditor } from '@/components/transcription-title-editor'
import { TranscriptionGetResponse } from '@/lib/client'
import { getRecordingsForTranscriptionTranscriptionsTranscriptionIdRecordingsGetOptions } from '@/lib/client/@tanstack/react-query.gen'
import { useQuery } from '@tanstack/react-query'

export const TranscriptionHeader = ({
  transcription,
  dateLabel,
}: {
  transcription: TranscriptionGetResponse
  dateLabel: string
}) => (
  <>
    <TranscriptionTitleEditor
      title={transcription.title}
      transcriptionId={transcription.id}
      status={transcription.status}
    />
    <div className="govuk-!-margin-bottom-4 flex items-center gap-2">
      <StatusBadge status={transcription.status} />
      <span className="govuk-body-s govuk-!-margin-bottom-0">{dateLabel}</span>
    </div>
  </>
)

export const AudioPlayer = ({
  transcriptionId,
}: {
  transcriptionId: string
}) => {
  const { data: recordings } = useQuery({
    ...getRecordingsForTranscriptionTranscriptionsTranscriptionIdRecordingsGetOptions(
      { path: { transcription_id: transcriptionId } }
    ),
  })
  if (!recordings || recordings.length == 0) {
    return null
  }
  return (
    <div className="mb-2 flex w-full max-w-3xl flex-col gap-2 rounded border bg-white p-2">
      <audio controls src={recordings[0].url} className="w-full" />
      <div className="flex justify-end">
        <DownloadButton recordings={recordings} />
      </div>
    </div>
  )
}

export const StatusNotificationPage = ({
  transcription,
  dateLabel,
  title,
  children,
}: {
  transcription: TranscriptionGetResponse
  dateLabel: string
  title: string
  children: React.ReactNode
}) => (
  <div>
    <TranscriptionHeader transcription={transcription} dateLabel={dateLabel} />
    <GovukNotificationBanner title={title}>
      <p className="govuk-notification-banner__heading">{children}</p>
    </GovukNotificationBanner>
    <AudioPlayer transcriptionId={transcription.id} />
  </div>
)
