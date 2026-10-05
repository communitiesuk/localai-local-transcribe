import { renderHook } from '@testing-library/react'
import { useMutation } from '@tanstack/react-query'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useStartTranscription } from '@/hooks/use-start-transcription'
import { recordAnalyticsEvent } from '@/lib/analytics'

vi.mock('@/lib/analytics', () => ({
  recordAnalyticsEvent: vi.fn(),
}))

vi.mock('@/providers/transcription-db-provider', () => ({
  useRecordingDb: () => ({ removeRecording: vi.fn() }),
}))

vi.mock('@/lib/client/@tanstack/react-query.gen', () => ({
  createRecordingRecordingsPostMutation: () => ({
    mutationKey: ['createRecording'],
  }),
  createTranscriptionTranscriptionsPostMutation: () => ({
    mutationKey: ['createTranscription'],
  }),
}))

vi.mock('@tanstack/react-query', () => ({
  useMutation: vi.fn(),
}))

describe('useStartTranscription', () => {
  const createTranscription = vi.fn()
  const createRecording = vi.fn()
  const uploadBlob = vi.fn()

  const submit = (file: Blob | File) => {
    const { result } = renderHook(() => useStartTranscription())
    return result.current.onSubmit(
      { file, title: 'Test' },
      new AbortController().signal
    )
  }

  beforeEach(() => {
    vi.clearAllMocks()
    // jsdom never fires loadedmetadata, so the duration lookup would hang. It is not what these tests are about.
    Object.defineProperty(URL, 'createObjectURL', {
      configurable: true,
      value: undefined,
    })
    createTranscription.mockResolvedValue({ id: 'transcription-1' })
    createRecording.mockResolvedValue({
      id: 'recording-1',
      upload_url: 'https://uploads.test/recording-1',
    })
    uploadBlob.mockResolvedValue(undefined)

    vi.mocked(useMutation).mockImplementation((options: unknown) => {
      const mutationKey = (options as { mutationKey?: string[] }).mutationKey
      if (mutationKey?.[0] === 'createTranscription') {
        return { mutateAsync: createTranscription, isPending: false } as never
      }
      if (mutationKey?.[0] === 'createRecording') {
        return { mutateAsync: createRecording, isPending: false } as never
      }
      return { mutateAsync: uploadBlob, isPending: false } as never
    })
  })

  it('records the upload and transcript events for a live recording', async () => {
    await submit(new Blob(['audio']))

    expect(recordAnalyticsEvent).toHaveBeenCalledWith(
      'audio_upload_complete_from_live_recording'
    )
    expect(recordAnalyticsEvent).toHaveBeenCalledWith(
      'transcript_requested_for_live_recording'
    )
    expect(recordAnalyticsEvent).not.toHaveBeenCalledWith(
      'live_recording_started_or_upload_requested'
    )
  })

  it('records the upload requested event and the direct upload events for a file', async () => {
    await submit(new File(['audio'], 'meeting.mp3', { type: 'audio/mpeg' }))

    expect(recordAnalyticsEvent).toHaveBeenNthCalledWith(
      1,
      'live_recording_started_or_upload_requested'
    )
    expect(recordAnalyticsEvent).toHaveBeenCalledWith(
      'audio_upload_complete_from_direct_upload'
    )
    expect(recordAnalyticsEvent).toHaveBeenCalledWith(
      'transcript_requested_for_direct_upload'
    )
  })

  it('records nothing once the upload fails', async () => {
    uploadBlob.mockRejectedValue(new Error('Failed to upload file'))

    await expect(submit(new Blob(['audio']))).rejects.toThrow(
      'Failed to upload file'
    )

    expect(recordAnalyticsEvent).not.toHaveBeenCalledWith(
      'audio_upload_complete_from_live_recording'
    )
    expect(recordAnalyticsEvent).not.toHaveBeenCalledWith(
      'transcript_requested_for_live_recording'
    )
  })
})
