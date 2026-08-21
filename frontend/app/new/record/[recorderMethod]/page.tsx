'use client'

import { useParams } from 'next/navigation'
import { MicRecorderForm } from '@/components/audio/mic-recorder'
import { TabRecorderForm } from '@/components/audio/tab-recorder/tab-recorder'
import { GovukBackLink, GovukHeading } from '@/components/govuk'
import {
  useRecordingUiStore,
  type RecordingState,
  type RecordingUiStore,
} from '@/stores/use-recording-ui-store'
import { notFound } from 'next/navigation'

type RecorderMethod = 'in-person' | 'online'
const recorderMethods: RecorderMethod[] = ['in-person', 'online']

const titleMapper: Record<RecordingState, string | boolean> = {
  idle: 'Select a microphone',
  starting: false,
  recording: 'Recording in progress',
  paused: 'Recording paused',
  stopConfirm: 'Are you sure you want to stop recording?',
  stopped: false,
}

const showBackLink: RecordingState[] = [
  'idle',
  'recording',
  'paused',
  'stopped',
]

export default function RecordPage() {
  const params = useParams<{ recorderMethod: RecorderMethod }>()
  const recorderMethod = params.recorderMethod

  const recordingState = useRecordingUiStore(
    (state: RecordingUiStore) => state.recordingState
  )

  const recorderForm =
    recorderMethod === 'in-person' ? <MicRecorderForm /> : <TabRecorderForm />

  if (!recorderMethods.includes(recorderMethod)) {
    notFound()
  }

  return (
    <div>
      {showBackLink.includes(recordingState) && <GovukBackLink href="/" />}
      {titleMapper[recordingState] && (
        <GovukHeading>{titleMapper[recordingState]}</GovukHeading>
      )}
      {recorderForm}
    </div>
  )
}
