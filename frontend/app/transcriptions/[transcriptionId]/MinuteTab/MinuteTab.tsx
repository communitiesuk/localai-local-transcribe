'use client'

import { MinuteEditor } from '@/app/transcriptions/[transcriptionId]/MinuteTab/minute-editor/minute-editor'
import { NewMinuteDialog } from '@/app/transcriptions/[transcriptionId]/MinuteTab/NewMinuteDialog'
import { AudioWav } from '@/components/icons/AudioWav'
import { TranscriptionGetResponse } from '@/lib/client'
import { listMinutesForTranscriptionTranscriptionTranscriptionIdMinutesGetOptions } from '@/lib/client/@tanstack/react-query.gen'
import { useQuery } from '@tanstack/react-query'
import { AudioWaveform } from 'lucide-react'
import { useState } from 'react'

export function MinuteTab({
  transcription,
}: {
  transcription: TranscriptionGetResponse
}) {
  const { data: minutes = [], isLoading } = useQuery({
    ...listMinutesForTranscriptionTranscriptionTranscriptionIdMinutesGetOptions(
      {
        path: { transcription_id: transcription.id! },
      }
    ),
  })
  // Only see most recent minute of each template type
  const [selectedMinute, setSelectedMinute] = useState(0)
  const safeSelectedMinute = Math.min(
    selectedMinute,
    Math.max(minutes.length - 1, 0)
  )

  if (isLoading) {
    return (
      <div className="flex w-full flex-col items-center justify-center">
        <AudioWav />
      </div>
    )
  }
  if (minutes.length == 0) {
    return (
      <div className="mt-4 flex flex-col items-center justify-center gap-2 text-slate-500">
        <AudioWaveform />
        <p>No minutes generated yet.</p>
        <div>
          <NewMinuteDialog transcriptionId={transcription.id!} />
        </div>
      </div>
    )
  }
  return (
    <>
      <MinuteEditor
        transcription={transcription}
        minute={minutes[safeSelectedMinute]}
      />
    </>
  )
}
