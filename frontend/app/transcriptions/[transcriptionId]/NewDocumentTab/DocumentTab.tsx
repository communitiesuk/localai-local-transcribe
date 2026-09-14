import { MinuteListItem, TranscriptionGetResponse } from '@/lib/client'
import { MinuteEditor } from '@/app/transcriptions/[transcriptionId]/MinuteTab/minute-editor/minute-editor'

export const DocumentTab = ({
  transcription,
  minute,
  onActivityChange,
}: {
  transcription: TranscriptionGetResponse
  minute: MinuteListItem
  onActivityChange?: (busy: boolean) => void
}) => {
  return (
    <MinuteEditor
      transcription={transcription}
      minute={minute}
      onActivityChange={onActivityChange}
    />
  )
}
