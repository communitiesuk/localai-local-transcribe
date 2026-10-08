import { MinuteListItem, TranscriptionGetResponse } from '@/lib/client'
import { MinuteEditor } from '@/app/transcriptions/[transcriptionId]/MinuteTab/minute-editor/minute-editor'

export const DocumentTab = ({
  transcription,
  minute,
  onActivityChange,
  onCitationClicked,
  onRemoved,
}: {
  transcription: TranscriptionGetResponse
  minute: MinuteListItem
  onActivityChange?: (busy: boolean) => void
  onCitationClicked?: (citationIndex: number) => void
  onRemoved: () => void
}) => {
  return (
    <MinuteEditor
      transcription={transcription}
      minute={minute}
      onActivityChange={onActivityChange}
      onCitationClicked={onCitationClicked}
      onRemoved={onRemoved}
    />
  )
}
