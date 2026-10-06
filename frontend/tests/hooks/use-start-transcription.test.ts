import { renderHook } from '@testing-library/react'
import { useMutation, useQuery } from '@tanstack/react-query'
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
  getUserUsersMeGetOptions: () => ({ queryKey: ['user'] }),
}))

vi.mock('@tanstack/react-query', () => ({
  useMutation: vi.fn(),
  useQuery: vi.fn(),
}))

const ORGANISATION_ID = 'a3f1c2d4-5e6f-4a7b-8c9d-0e1f2a3b4c5d'

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
    vi.mocked(useQuery).mockReturnValue({
      data: { organisation_id: ORGANISATION_ID },
    } as never)

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
      'audio_upload_complete_from_live_recording',
      { organisation_id: ORGANISATION_ID }
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
      'audio_upload_complete_from_direct_upload',
      { organisation_id: ORGANISATION_ID }
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
      'audio_upload_complete_from_live_recording',
      { organisation_id: ORGANISATION_ID }
    )
    expect(recordAnalyticsEvent).not.toHaveBeenCalledWith(
      'transcript_requested_for_live_recording'
    )
  })

  it('sends no organisation when the user has none', async () => {
    vi.mocked(useQuery).mockReturnValue({
      data: { organisation_id: null },
    } as never)

    await submit(new Blob(['audio']))

    expect(recordAnalyticsEvent).toHaveBeenCalledWith(
      'audio_upload_complete_from_live_recording',
      undefined
    )
  })
})
