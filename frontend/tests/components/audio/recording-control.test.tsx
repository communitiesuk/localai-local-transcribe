import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import RecordingControl from '@/components/audio/recording-control'

describe('<RecordingControl />', () => {
  it('names the microphone in use above the recording length', () => {
    render(
      <RecordingControl
        stream={null}
        isRecording={true}
        microphoneLabel="Default - External Microphone (Built-in)"
        onStopRecording={vi.fn()}
        recordingDuration={0}
      />
    )

    const microphone = screen.getByText(
      'Microphone in use: Default - External Microphone (Built-in)'
    )
    const length = screen.getByText(/Recording length:/)

    expect(microphone).toBeInTheDocument()
    expect(
      microphone.compareDocumentPosition(length) &
        Node.DOCUMENT_POSITION_FOLLOWING
    ).toBeTruthy()
  })

  it('says explicitly when there is no microphone, so a tab only recording is clear', () => {
    render(
      <RecordingControl
        stream={null}
        isRecording={true}
        noMicrophone={true}
        onStopRecording={vi.fn()}
        recordingDuration={0}
      />
    )

    expect(
      screen.getByText('No microphone in use, recording tab audio only')
    ).toBeInTheDocument()
    expect(screen.queryByText(/Microphone in use:/)).not.toBeInTheDocument()
  })

  it('shows no microphone line when the device is unknown', () => {
    render(
      <RecordingControl
        stream={null}
        isRecording={true}
        onStopRecording={vi.fn()}
        recordingDuration={0}
      />
    )

    expect(screen.queryByText(/Microphone in use:/)).not.toBeInTheDocument()
  })

  it('shows the recording length', () => {
    render(
      <RecordingControl
        stream={null}
        isRecording={true}
        onStopRecording={vi.fn()}
        recordingDuration={3_725_000}
      />
    )

    expect(screen.getByText('Recording length: 01:02:05')).toBeInTheDocument()
  })
})
