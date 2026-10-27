import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as Sentry from '@sentry/nextjs'

import {
  AudioUploadForm,
  UNSUPPORTED_FORMAT_MESSAGE,
} from '@/components/audio/AudioUploadForm'
import { recordAnalyticsEvent } from '@/lib/analytics'
import { useUploadRecordingStore } from '@/stores/use-upload-recording-store'

vi.mock('@/lib/analytics', () => ({
  recordAnalyticsEvent: vi.fn(),
}))

vi.mock('@sentry/nextjs', () => ({
  captureException: vi.fn(),
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
      'audio_upload_requested'
    )
  })
  const dropFile = (file: File) => {
    const dropzone = document.querySelector('.border-2') as HTMLElement

    fireEvent.drop(dropzone, {
      dataTransfer: { files: [file], types: ['Files'] },
    })
  }

  it('explains that the format is not supported when one is rejected', async () => {
    render(<AudioUploadForm />)

    dropFile(new File(['notes'], 'client notes.txt', { type: 'text/plain' }))

    expect(
      await screen.findByText(UNSUPPORTED_FORMAT_MESSAGE)
    ).toBeInTheDocument()
  })

  it('reports the rejected format to Sentry without the filename', async () => {
    render(<AudioUploadForm />)

    dropFile(new File(['notes'], 'client notes.txt', { type: 'text/plain' }))

    await screen.findByText(UNSUPPORTED_FORMAT_MESSAGE)

    expect(Sentry.captureException).toHaveBeenCalledOnce()
    const [error, context] = vi.mocked(Sentry.captureException).mock.calls[0]
    expect((error as Error).message).toBe('Unsupported upload file format')
    expect(context).toMatchObject({
      extra: { fileType: 'text/plain', fileExtension: '.txt' },
    })
  })

  it('accepts a supported format', async () => {
    render(<AudioUploadForm />)

    dropFile(new File(['audio'], 'meeting.mp3', { type: 'audio/mpeg' }))

    expect(
      screen.queryByText(UNSUPPORTED_FORMAT_MESSAGE)
    ).not.toBeInTheDocument()
    expect(Sentry.captureException).not.toHaveBeenCalled()
  })
})
