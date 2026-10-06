import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { AudioUploadForm } from '@/components/audio/AudioUploadForm'
import { recordAnalyticsEvent } from '@/lib/analytics'
import { useUploadRecordingStore } from '@/stores/use-upload-recording-store'

vi.mock('@/lib/analytics', () => ({
  recordAnalyticsEvent: vi.fn(),
}))

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn() }),
}))

vi.mock('@/hooks/use-start-transcription', async () => {
  const { useForm } =
    await vi.importActual<typeof import('react-hook-form')>('react-hook-form')

  return {
    useStartTranscription: () => ({
      isPending: false,
      onSubmit: vi.fn(),
      form: useForm({
        defaultValues: {
          file: new File(['audio'], 'meeting.mp3', { type: 'audio/mpeg' }),
        },
      }),
    }),
  }
})

describe('<AudioUploadForm />', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    useUploadRecordingStore.setState({ startUpload: vi.fn() })
  })

  it('records the upload requested event once, when the upload is requested', async () => {
    render(<AudioUploadForm />)

    await userEvent.click(screen.getByRole('button', { name: 'Upload' }))

    expect(recordAnalyticsEvent).toHaveBeenCalledExactlyOnceWith(
      'live_recording_started_or_upload_requested'
    )
  })
})
