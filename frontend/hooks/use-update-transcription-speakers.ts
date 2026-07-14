import { useQueryClient } from '@tanstack/react-query'
import { useCallback } from 'react'

import {
  getTranscriptionTranscriptionsTranscriptionIdGetQueryKey,
  listTranscriptionsTranscriptionsGetQueryKey,
} from '@/lib/client/@tanstack/react-query.gen'
import {
  renameSpeakerEverywhereTranscriptionsTranscriptionIdSpeakersPatch,
  type RenameSpeakerRequest,
  updateDialogueEntrySpeakerTranscriptionsTranscriptionIdDialogueEntriesEntryIndexSpeakerPatch,
  type UpdateDialogueEntrySpeakerRequest,
  updateDialogueEntryTextTranscriptionsTranscriptionIdDialogueEntriesEntryIndexTextPatch,
  type UpdateDialogueEntryTextRequest,
  updateTranscriptionTitleTranscriptionsTranscriptionIdTitlePatch,
} from '@/lib/client'

export const useUpdateTranscriptionSpeakers = (transcriptionId: string) => {
  const queryClient = useQueryClient()

  const invalidateTranscription = useCallback(async () => {
    await queryClient.invalidateQueries({
      queryKey: getTranscriptionTranscriptionsTranscriptionIdGetQueryKey({
        path: { transcription_id: transcriptionId },
      }),
    })
  }, [queryClient, transcriptionId])

  const renameSpeakerEverywhere = useCallback(
    async (body: RenameSpeakerRequest) => {
      await renameSpeakerEverywhereTranscriptionsTranscriptionIdSpeakersPatch({
        path: { transcription_id: transcriptionId },
        body,
        throwOnError: true,
      })
      await invalidateTranscription()
    },
    [invalidateTranscription, transcriptionId]
  )

  const updateDialogueEntrySpeaker = useCallback(
    async (entryIndex: number, body: UpdateDialogueEntrySpeakerRequest) => {
      await updateDialogueEntrySpeakerTranscriptionsTranscriptionIdDialogueEntriesEntryIndexSpeakerPatch(
        {
          path: {
            transcription_id: transcriptionId,
            entry_index: entryIndex,
          },
          body,
          throwOnError: true,
        }
      )
      await invalidateTranscription()
    },
    [invalidateTranscription, transcriptionId]
  )

  return { renameSpeakerEverywhere, updateDialogueEntrySpeaker }
}

export const useUpdateTranscription = (transcriptionId: string) => {
  const queryClient = useQueryClient()

  const invalidateTranscription = useCallback(async () => {
    await queryClient.invalidateQueries({
      queryKey: getTranscriptionTranscriptionsTranscriptionIdGetQueryKey({
        path: { transcription_id: transcriptionId },
      }),
    })
  }, [queryClient, transcriptionId])

  const updateDialogueEntryText = useCallback(
    async (entryIndex: number, body: UpdateDialogueEntryTextRequest) => {
      await updateDialogueEntryTextTranscriptionsTranscriptionIdDialogueEntriesEntryIndexTextPatch(
        {
          path: {
            transcription_id: transcriptionId,
            entry_index: entryIndex,
          },
          body,
          throwOnError: true,
        }
      )
      await invalidateTranscription()
    },
    [invalidateTranscription, transcriptionId]
  )

  const updateTitle = useCallback(
    async (title: string | null | undefined) => {
      const normalizedTitle = title || null
      await updateTranscriptionTitleTranscriptionsTranscriptionIdTitlePatch({
        path: { transcription_id: transcriptionId },
        body: { title: normalizedTitle },
        throwOnError: true,
      })
      await Promise.all([
        invalidateTranscription(),
        queryClient.invalidateQueries({
          queryKey: listTranscriptionsTranscriptionsGetQueryKey(),
        }),
      ])
    },
    [invalidateTranscription, queryClient, transcriptionId]
  )

  return { updateDialogueEntryText, updateTitle }
}
