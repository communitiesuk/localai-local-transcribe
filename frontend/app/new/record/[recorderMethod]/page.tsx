'use client'

import { useParams } from 'next/navigation'
import { MicRecorderForm } from '@/components/audio/mic-recorder'
import { TabRecorderForm } from '@/components/audio/tab-recorder/tab-recorder'
import { GovukBackLink, GovukHeading } from '@/components/govuk'
import { useRecordingUiStore } from '@/stores/use-recording-ui-store'

type RecorderMethod = 'in-person' | 'online'

const titleMapper = {
  idle: 'Select a Microphone',
  recording: 'Recording in progress',
  paused: 'Recording Paused',
  review: 'Are you sure you want to stop recording?',
}

export default function RecordPage() {
  const params = useParams<{ recorderMethod: RecorderMethod }>()
  const recorderMethod = params.recorderMethod
  const { recordingState } = useRecordingUiStore()

  return (
    <div>
      {recordingState !== 'review' && <GovukBackLink href="/" />}
      <GovukHeading>{titleMapper[recordingState]}</GovukHeading>
      {recorderMethod === 'in-person' ? (
        <MicRecorderForm />
      ) : (
        <TabRecorderForm />
      )}
    </div>
  )
}
