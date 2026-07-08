import { renderHook, act } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import {
  useUpdateTranscription,
  useUpdateTranscriptionSpeakers,
} from '@/hooks/use-update-transcription-speakers'
import {
  renameSpeakerEverywhereTranscriptionsTranscriptionIdSpeakersPatch,
  updateDialogueEntrySpeakerTranscriptionsTranscriptionIdDialogueEntriesEntryIndexSpeakerPatch,
  updateDialogueEntryTextTranscriptionsTranscriptionIdDialogueEntriesEntryIndexTextPatch,
  updateTranscriptionTitleTranscriptionsTranscriptionIdTitlePatch,
} from '@/lib/client'
import {
  getTranscriptionTranscriptionsTranscriptionIdGetQueryKey,
  listTranscriptionsTranscriptionsGetQueryKey,
} from '@/lib/client/@tanstack/react-query.gen'
import { useQueryClient } from '@tanstack/react-query'

vi.mock('@tanstack/react-query', () => ({
  useQueryClient: vi.fn(),
}))

vi.mock('@/lib/client', () => ({
  renameSpeakerEverywhereTranscriptionsTranscriptionIdSpeakersPatch: vi.fn(),
  updateDialogueEntrySpeakerTranscriptionsTranscriptionIdDialogueEntriesEntryIndexSpeakerPatch:
    vi.fn(),
  updateDialogueEntryTextTranscriptionsTranscriptionIdDialogueEntriesEntryIndexTextPatch:
    vi.fn(),
  updateTranscriptionTitleTranscriptionsTranscriptionIdTitlePatch: vi.fn(),
}))

vi.mock('@/lib/client/@tanstack/react-query.gen', () => ({
  getTranscriptionTranscriptionsTranscriptionIdGetQueryKey: vi.fn(),
  listTranscriptionsTranscriptionsGetQueryKey: vi.fn(),
}))

describe('use-update-transcription-speakers hooks', () => {
  const invalidateQueries = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(useQueryClient).mockReturnValue({ invalidateQueries } as never)
    vi.mocked(
      getTranscriptionTranscriptionsTranscriptionIdGetQueryKey
    ).mockReturnValue(['transcription'] as never)
    vi.mocked(listTranscriptionsTranscriptionsGetQueryKey).mockReturnValue([
      'transcriptions',
    ] as never)

    vi.mocked(
      renameSpeakerEverywhereTranscriptionsTranscriptionIdSpeakersPatch
    ).mockResolvedValue({} as never)
    vi.mocked(
      updateDialogueEntrySpeakerTranscriptionsTranscriptionIdDialogueEntriesEntryIndexSpeakerPatch
    ).mockResolvedValue({} as never)
    vi.mocked(
      updateDialogueEntryTextTranscriptionsTranscriptionIdDialogueEntriesEntryIndexTextPatch
    ).mockResolvedValue({} as never)
    vi.mocked(
      updateTranscriptionTitleTranscriptionsTranscriptionIdTitlePatch
    ).mockResolvedValue({} as never)
  })

  it('calls generated API and invalidates query for renameSpeakerEverywhere', async () => {
    const { result } = renderHook(() => useUpdateTranscriptionSpeakers('abc'))

    await act(async () => {
      await result.current.renameSpeakerEverywhere({
        original_speaker: 'Speaker 1',
        new_speaker: 'Alice',
      })
    })

    expect(
      renameSpeakerEverywhereTranscriptionsTranscriptionIdSpeakersPatch
    ).toHaveBeenCalledWith({
      path: { transcription_id: 'abc' },
      body: {
        original_speaker: 'Speaker 1',
        new_speaker: 'Alice',
      },
      throwOnError: true,
    })
    expect(invalidateQueries).toHaveBeenCalledWith({
      queryKey: ['transcription'],
    })
  })

  it('calls generated API and invalidates query for updateDialogueEntrySpeaker', async () => {
    const { result } = renderHook(() => useUpdateTranscriptionSpeakers('abc'))

    await act(async () => {
      await result.current.updateDialogueEntrySpeaker(3, {
        new_speaker: 'Bob',
        expected_speaker: 'Speaker 2',
      })
    })

    expect(
      updateDialogueEntrySpeakerTranscriptionsTranscriptionIdDialogueEntriesEntryIndexSpeakerPatch
    ).toHaveBeenCalledWith({
      path: {
        transcription_id: 'abc',
        entry_index: 3,
      },
      body: {
        new_speaker: 'Bob',
        expected_speaker: 'Speaker 2',
      },
      throwOnError: true,
    })
    expect(invalidateQueries).toHaveBeenCalledWith({
      queryKey: ['transcription'],
    })
  })

  it('calls generated API and invalidates query for updateDialogueEntryText', async () => {
    const { result } = renderHook(() => useUpdateTranscription('abc'))

    await act(async () => {
      await result.current.updateDialogueEntryText(1, {
        new_text: 'Updated text',
        expected_text: 'Old text',
      })
    })

    expect(
      updateDialogueEntryTextTranscriptionsTranscriptionIdDialogueEntriesEntryIndexTextPatch
    ).toHaveBeenCalledWith({
      path: {
        transcription_id: 'abc',
        entry_index: 1,
      },
      body: {
        new_text: 'Updated text',
        expected_text: 'Old text',
      },
      throwOnError: true,
    })
    expect(invalidateQueries).toHaveBeenCalledWith({
      queryKey: ['transcription'],
    })
  })

  it('calls generated API and invalidates transcription and list queries for updateTitle', async () => {
    const { result } = renderHook(() => useUpdateTranscription('abc'))

    await act(async () => {
      await result.current.updateTitle('New title')
    })

    expect(
      updateTranscriptionTitleTranscriptionsTranscriptionIdTitlePatch
    ).toHaveBeenCalledWith({
      path: { transcription_id: 'abc' },
      body: { title: 'New title' },
      throwOnError: true,
    })
    expect(invalidateQueries).toHaveBeenCalledWith({
      queryKey: ['transcription'],
    })
    expect(invalidateQueries).toHaveBeenCalledWith({
      queryKey: ['transcriptions'],
    })
  })

  it('normalizes empty title to null for updateTitle', async () => {
    const { result } = renderHook(() => useUpdateTranscription('abc'))

    await act(async () => {
      await result.current.updateTitle('')
    })

    expect(
      updateTranscriptionTitleTranscriptionsTranscriptionIdTitlePatch
    ).toHaveBeenCalledWith({
      path: { transcription_id: 'abc' },
      body: { title: null },
      throwOnError: true,
    })
  })
})
