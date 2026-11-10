import { act, fireEvent, render, screen } from '@testing-library/react'
import { useQuery } from '@tanstack/react-query'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { MicRecorderForm } from '@/components/audio/mic-recorder'
import { TabRecorderForm } from '@/components/audio/tab-recorder/tab-recorder'
import { useRecordingUIStore } from '@/stores/use-recording-ui-store'
import { useUploadRecordingStore } from '@/stores/use-upload-recording-store'

const { onSubmit } = vi.hoisted(() => ({ onSubmit: vi.fn() }))

vi.mock('@tanstack/react-query', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@tanstack/react-query')>()),
  useQuery: vi.fn(),
}))
vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn(), back: vi.fn() }),
}))
vi.mock('@/hooks/use-start-transcription', async () => {
  const { useForm } = await import('react-hook-form')
  return {
    useStartTranscription: () => ({
      form: useForm({ defaultValues: { file: null } }),
      onSubmit,
    }),
  }
})

let emitAudioData = true

const createTrack = () => ({
  stop: vi.fn(),
  enabled: true,
  kind: 'audioinput',
  label: 'Default mic',
  getSettings: () => ({ deviceId: 'default' }),
})

const createStream = () => {
  const tracks = [createTrack()]
  return {
    getTracks: () => tracks,
    getAudioTracks: () => tracks,
    addTrack: (track: ReturnType<typeof createTrack>) => tracks.push(track),
  }
}

class StubMediaRecorder {
  state: 'inactive' | 'recording' | 'paused' = 'inactive'
  onstart: (() => void) | null = null
  ondataavailable: ((event: { data: Blob }) => void) | null = null
  onstop: (() => void) | null = null
  onerror: (() => void) | null = null

  constructor(public stream: MediaStream) {}

  start() {
    this.state = 'recording'
    this.onstart?.()
  }

  pause() {
    this.state = 'paused'
  }

  resume() {
    this.state = 'recording'
  }

  stop() {
    this.state = 'inactive'
    if (emitAudioData) {
      this.ondataavailable?.({ data: new Blob(['audio']) })
    }
    this.onstop?.()
  }
}

class StubAudioContext {
  private node = { gain: { value: 0 }, connect: () => this.node }

  createGain() {
    return this.node
  }

  createAnalyser() {
    return { ...this.node, fftSize: 0, smoothingTimeConstant: 0 }
  }

  createMediaStreamSource() {
    return this.node
  }

  createMediaStreamDestination() {
    return { stream: createStream() }
  }

  close() {
    return Promise.resolve()
  }
}

class StubMediaStream {
  private tracks: unknown[] = []

  addTrack(track: unknown) {
    this.tracks.push(track)
  }

  getTracks() {
    return this.tracks
  }

  getAudioTracks() {
    return this.tracks
  }
}

const click = async (name: string) => {
  await act(async () => {
    fireEvent.click(screen.getByRole('button', { name }))
  })
}

const advance = async (ms: number) => {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(ms)
  })
}

const startRecording = async () => {
  await click('Start recording')

  // Wait 3 seconds, allowing a re-render inbetween each so the timer tracks it correctly
  for (let second = 0; second < 3; second++) {
    await advance(1000)
  }
  await advance(0)
}

const expectRecordingLength = (length: string) =>
  expect(screen.getByText(/Recording length:/)).toHaveTextContent(
    `Recording length: ${length}`
  )

const stopRecording = async () => {
  await click('Stop')
  await click('Stop Recording')
}

describe('recording duration', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.useFakeTimers()
    localStorage.clear()
    emitAudioData = true
    useRecordingUIStore.getState().resetRecordingUI()
    useUploadRecordingStore.getState().reset()
    vi.mocked(useQuery).mockReturnValue({
      data: { id: 'user-1' },
    } as ReturnType<typeof useQuery>)

    vi.stubGlobal('MediaRecorder', StubMediaRecorder)
    vi.stubGlobal('MediaStream', StubMediaStream)
    vi.stubGlobal('AudioContext', StubAudioContext)
    vi.stubGlobal(
      'ResizeObserver',
      class {
        observe() {}
        disconnect() {}
      }
    )
    // jsdom has no canvas, and the waveform skips drawing without a context
    HTMLCanvasElement.prototype.getContext = () => null
    Object.defineProperty(navigator, 'mediaDevices', {
      configurable: true,
      value: {
        getUserMedia: async () => createStream(),
        getDisplayMedia: async () => createStream(),
        enumerateDevices: async () => [
          { deviceId: 'default', kind: 'audioinput', label: 'Default mic' },
        ],
      },
    })
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.unstubAllGlobals()
  })

  const recorders = [
    { name: 'in-person', Recorder: MicRecorderForm },
    { name: 'online', Recorder: TabRecorderForm },
  ] as const

  const renderRecorder = async (
    Recorder: (typeof recorders)[number]['Recorder']
  ) => {
    render(<Recorder />)
    // The microphone permission step asks for devices as soon as it mounts
    await advance(0)
  }

  it.each(recorders)(
    'counts up while the $name recording runs',
    async ({ Recorder }) => {
      await renderRecorder(Recorder)
      await startRecording()

      await advance(5000)

      expectRecordingLength('00:00:05')
    }
  )

  it.each(recorders)(
    'leaves out paused time for the $name recorder',
    async ({ Recorder }) => {
      await renderRecorder(Recorder)
      await startRecording()

      await advance(2000)
      await click('Pause')
      await advance(10000)
      await click('Resume')
      await advance(1000)

      expectRecordingLength('00:00:03')
    }
  )

  it.each(recorders)(
    'submits the tracked length for the $name recording, as the browser leaves it out of the file',
    async ({ Recorder }) => {
      await renderRecorder(Recorder)
      await startRecording()

      await advance(7000)
      await stopRecording()

      expect(onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({ durationSeconds: 7 }),
        expect.anything()
      )
    }
  )

  it.each(recorders)(
    'starts the next $name recording from zero',
    async ({ Recorder }) => {
      emitAudioData = false
      await renderRecorder(Recorder)
      await startRecording()

      await advance(3000)
      await stopRecording()
      expect(screen.getByText(/No audio data was recorded/)).toBeInTheDocument()

      await startRecording()
      await advance(1000)

      expectRecordingLength('00:00:01')
    }
  )
})
