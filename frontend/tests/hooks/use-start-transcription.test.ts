import { renderHook } from '@testing-library/react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
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
  useQueryClient: vi.fn(),
}))

const ORGANISATION_ID = 'a3f1c2d4-5e6f-4a7b-8c9d-0e1f2a3b4c5d'

describe('useStartTranscription', () => {
  const createTranscription = vi.fn()
  const createRecording = vi.fn()
  const uploadBlob = vi.fn()
  const ensureQueryData = vi.fn()

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
    ensureQueryData.mockResolvedValue({ organisation_id: ORGANISATION_ID })
    vi.mocked(useQueryClient).mockReturnValue({ ensureQueryData } as never)

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
  })

  it('records the direct upload events for a file', async () => {
    await submit(new File(['audio'], 'meeting.mp3', { type: 'audio/mpeg' }))

    expect(recordAnalyticsEvent).toHaveBeenCalledWith(
      'audio_upload_complete_from_direct_upload',
      { organisation_id: ORGANISATION_ID }
    )
    expect(recordAnalyticsEvent).toHaveBeenCalledWith(
      'transcript_requested_for_direct_upload'
    )
  })

  it('leaves the upload requested event to the form, so a retry cannot double count it', async () => {
    await submit(new File(['audio'], 'meeting.mp3', { type: 'audio/mpeg' }))

    expect(recordAnalyticsEvent).not.toHaveBeenCalledWith(
      'audio_upload_requested'
    )
  })

  it('tells the backend where the audio came from', async () => {
    await submit(new File(['audio'], 'meeting.mp3', { type: 'audio/mpeg' }))
    expect(createRecording).toHaveBeenCalledWith(
      expect.objectContaining({
        body: expect.objectContaining({ source: 'direct_upload' }),
      })
    )

    await submit(new Blob(['audio']))
    expect(createRecording).toHaveBeenCalledWith(
      expect.objectContaining({
        body: expect.objectContaining({ source: 'live_recording' }),
      })
    )
  })

  it('waits for the organisation rather than dropping it mid flight', async () => {
    let resolveUser: (user: { organisation_id: string }) => void = () => {}
    ensureQueryData.mockReturnValue(
      new Promise<{ organisation_id: string }>((resolve) => {
        resolveUser = resolve
      })
    )

    const pending = submit(new Blob(['audio']))
    resolveUser({ organisation_id: ORGANISATION_ID })
    await pending

    expect(recordAnalyticsEvent).toHaveBeenCalledWith(
      'audio_upload_complete_from_live_recording',
      { organisation_id: ORGANISATION_ID }
    )
  })

  it('still records the event when the organisation cannot be read', async () => {
    ensureQueryData.mockRejectedValue(new Error('offline'))

    await submit(new Blob(['audio']))

    expect(recordAnalyticsEvent).toHaveBeenCalledWith(
      'audio_upload_complete_from_live_recording',
      undefined
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
})
