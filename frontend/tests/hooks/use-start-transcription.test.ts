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

  beforeEach(() => {
    vi.clearAllMocks()
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

  describe('a live recording', () => {
    it('stores the recording as a live recording', async () => {
      const { result } = renderHook(() => useStartTranscription())

      await result.current.onSubmit({
        file: new Blob(['audio']),
        title: 'Test',
      })

      expect(createRecording).toHaveBeenCalledWith({
        body: expect.objectContaining({ source: 'live_recording' }),
      })
    })

    it('records the upload event for a live recording', async () => {
      const { result } = renderHook(() => useStartTranscription())

      await result.current.onSubmit({
        file: new Blob(['audio']),
        title: 'Test',
      })

      expect(recordAnalyticsEvent).toHaveBeenCalledWith(
        'audio_upload_complete_from_live_recording'
      )
    })

    it('does not record an upload requested event, as recording already started', async () => {
      const { result } = renderHook(() => useStartTranscription())

      await result.current.onSubmit({
        file: new Blob(['audio']),
        title: 'Test',
      })

      expect(recordAnalyticsEvent).not.toHaveBeenCalledWith(
        'live_recording_started_or_upload_requested'
      )
    })
  })

  describe('a direct upload', () => {
    const uploadedFile = () =>
      new File(['audio'], 'meeting.mp3', { type: 'audio/mpeg' })

    it('stores the recording as a direct upload', async () => {
      const { result } = renderHook(() => useStartTranscription())

      await result.current.onSubmit({ file: uploadedFile(), title: 'Test' })

      expect(createRecording).toHaveBeenCalledWith({
        body: expect.objectContaining({ source: 'direct_upload' }),
      })
    })

    it('records the upload requested event and then the upload event', async () => {
      const { result } = renderHook(() => useStartTranscription())

      await result.current.onSubmit({ file: uploadedFile(), title: 'Test' })

      expect(recordAnalyticsEvent).toHaveBeenNthCalledWith(
        1,
        'live_recording_started_or_upload_requested'
      )
      expect(recordAnalyticsEvent).toHaveBeenNthCalledWith(
        2,
        'audio_upload_complete_from_direct_upload'
      )
    })
  })

  it('does not record the upload event when the upload fails', async () => {
    uploadBlob.mockRejectedValue(new Error('Failed to upload file'))
    const { result } = renderHook(() => useStartTranscription())

    await expect(
      result.current.onSubmit({ file: new Blob(['audio']), title: 'Test' })
    ).rejects.toThrow('Failed to upload file')

    expect(recordAnalyticsEvent).not.toHaveBeenCalledWith(
      'audio_upload_complete_from_live_recording'
    )
  })
})