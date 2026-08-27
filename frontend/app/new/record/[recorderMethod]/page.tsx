'use client'

import { useParams } from 'next/navigation'
import { MicRecorderForm } from '@/components/audio/mic-recorder'
import { TabRecorderForm } from '@/components/audio/tab-recorder/tab-recorder'
import { GovukBackLink, GovukHeading } from '@/components/govuk'
import {
  useRecordingUIStore,
  type RecordingState,
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
  stopping: 'Are you sure you want to stop recording?',
  stopped: false,
}

const statesWithBackLink: RecordingState[] = [
  'idle',
  'recording',
  'paused',
  'stopped',
]

function RecordingIcon({ state }: { state: RecordingState }) {
  const colour =
    state === 'recording' ? '#D4351C' : state === 'paused' ? '#B1B4B6' : null

  if (!colour) {
    return null
  }

  return (
    <svg
      aria-hidden="true"
      focusable="false"
      xmlns="http://www.w3.org/2000/svg"
      width="40"
      height="40"
      viewBox="0 0 40 40"
      fill="none"
    >
      <circle cx="20" cy="20" r="19" stroke={colour} strokeWidth="2" />
      <circle cx="20" cy="20" r="12" fill={colour} />
    </svg>
  )
}

export default function RecordPage() {
  const params = useParams<{ recorderMethod: RecorderMethod }>()
  const recorderMethod = params.recorderMethod
  const { recordingUIState } = useRecordingUIStore()

  const recorderForm =
    recorderMethod === 'in-person' ? <MicRecorderForm /> : <TabRecorderForm />

  if (!recorderMethods.includes(recorderMethod)) {
    notFound()
  }

  return (
    <div>
      {statesWithBackLink.includes(recordingUIState) && (
        <GovukBackLink href="/" />
      )}
      {titleMapper[recordingUIState] && (
        <div className="flex gap-2">
          <RecordingIcon state={recordingUIState} />
          <GovukHeading>{titleMapper[recordingUIState]}</GovukHeading>
        </div>
      )}
      {recorderForm}
    </div>
  )
}
