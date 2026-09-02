import { MinuteListItem, TranscriptionGetResponse } from '@/lib/client'
import { MinuteEditor } from '@/app/transcriptions/[transcriptionId]/MinuteTab/minute-editor/minute-editor'

export const DocumentTab = ({
  transcription,
  minute,
}: {
  transcription: TranscriptionGetResponse
  minute: MinuteListItem
}) => {
  return <MinuteEditor transcription={transcription} minute={minute} />
}
