import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import RecordingControl from '@/components/audio/recording-control'
import { useRecordingUIStore } from '@/stores/use-recording-ui-store'

describe('<RecordingControl />', () => {
  beforeEach(() => {
    useRecordingUIStore.getState().resetRecordingUI()
  })

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
  it('tells the user how long a recording can be', () => {
    render(
      <RecordingControl
        stream={null}
        isRecording={true}
        onStopRecording={vi.fn()}
        recordingDuration={0}
      />
    )

    const limit = screen.getByText('Your recording must be 2 hours or less.')
    const length = screen.getByText(/Recording length:/)

    expect(limit).toBeInTheDocument()
    expect(
      length.compareDocumentPosition(limit) & Node.DOCUMENT_POSITION_FOLLOWING
    ).toBeTruthy()
  })

  it('keeps recording while the length is under the limit', () => {
    const onStopRecording = vi.fn()

    render(
      <RecordingControl
        stream={null}
        isRecording={true}
        onStopRecording={onStopRecording}
        recordingDuration={7_199_000}
      />
    )

    expect(onStopRecording).not.toHaveBeenCalled()
  })

  it('stops the recording once it reaches the limit', () => {
    const onStopRecording = vi.fn()

    render(
      <RecordingControl
        stream={null}
        isRecording={true}
        onStopRecording={onStopRecording}
        recordingDuration={7_200_000}
      />
    )

    expect(onStopRecording).toHaveBeenCalledTimes(1)
    expect(useRecordingUIStore.getState().recordingUIState).toBe('stopping')
  })

  it('says the limit stopped the recording, rather than asking to confirm', () => {
    render(
      <RecordingControl
        stream={null}
        isRecording={true}
        onStopRecording={vi.fn()}
        recordingDuration={7_200_000}
      />
    )

    expect(
      screen.getByText(/This recording reached 2 hours and has stopped\./)
    ).toBeInTheDocument()
    expect(
      screen.queryByRole('button', { name: 'Stop Recording' })
    ).not.toBeInTheDocument()
  })
})
