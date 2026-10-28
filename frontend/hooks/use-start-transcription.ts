import {
  createRecordingRecordingsPostMutation,
  createTranscriptionTranscriptionsPostMutation,
  getUserUsersMeGetOptions,
} from '@/lib/client/@tanstack/react-query.gen'
import { recordAnalyticsEvent } from '@/lib/analytics'
import { getFileExtension } from '@/lib/getFileExtension'
import { useRecordingDb } from '@/providers/transcription-db-provider'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useCallback } from 'react'
import { useForm } from 'react-hook-form'

export type TranscriptionForm = {
  file: Blob | File | null
  recordingId?: string
  title?: string
  recordedAt?: Date
}

const getMediaDurationSeconds = async (file: Blob | File) =>
  new Promise<number | undefined>((resolve) => {
    if (
      typeof document === 'undefined' ||
      typeof URL.createObjectURL !== 'function'
    ) {
      resolve(undefined)
      return
    }

    const media = document.createElement(
      file.type.startsWith('video/') ? 'video' : 'audio'
    )
    const objectUrl = URL.createObjectURL(file)

    const finish = (duration?: number) => {
      URL.revokeObjectURL(objectUrl)
      resolve(duration)
    }

    media.preload = 'metadata'
    media.onloadedmetadata = () => {
      finish(Number.isFinite(media.duration) ? media.duration : undefined)
    }
    media.onerror = () => {
      finish()
    }
    media.src = objectUrl
  })

export const useStartTranscription = (
  defaultValues?: Partial<TranscriptionForm>
) => {
  const { removeRecording } = useRecordingDb()
  const queryClient = useQueryClient()

  const getOrganisationId = useCallback(async () => {
    try {
      const user = await queryClient.ensureQueryData(getUserUsersMeGetOptions())
      return user.organisation_id
        ? { organisation_id: user.organisation_id }
        : undefined
    } catch {
      return undefined
    }
  }, [queryClient])

  const { mutateAsync: createTranscription, isPending: isCreating } =
    useMutation({
      ...createTranscriptionTranscriptionsPostMutation(),
    })

  const { mutateAsync: createRecording, isPending: isConfirming } = useMutation(
    {
      ...createRecordingRecordingsPostMutation(),
    }
  )

  const { mutateAsync: uploadBlob, isPending: isUploading } = useMutation({
    mutationFn: async ({
      uploadUrl,
      file,
      signal,
    }: {
      uploadUrl: string
      file: Blob | File
      signal?: AbortSignal
    }) => {
      const uploadResponse = await fetch(uploadUrl, {
        method: 'PUT',
        body: file,
        headers: {
          'x-ms-blob-type': 'BlockBlob',
        },
        signal,
      })

      if (!uploadResponse.ok) {
        throw new Error('Failed to upload file')
      }
    },
  })

  const onSubmit = useCallback(
    async (
      { file, recordingId, title }: TranscriptionForm,
      signal: AbortSignal
    ) => {
      if (!file) {
        return null
      }

      const isFile = file instanceof File

      const file_extension = isFile ? getFileExtension(file.name) : 'webm'
      const file_created_at =
        isFile && file.lastModified
          ? new Date(file.lastModified).toISOString()
          : undefined

      const recordingData = await createRecording({
        body: {
          file_extension,
          file_created_at,
          source: isFile ? 'direct_upload' : 'live_recording',
        },
        signal,
      })

      await uploadBlob({
        file,
        uploadUrl: recordingData.upload_url,
        signal,
      })

      recordAnalyticsEvent(
        isFile
          ? 'audio_upload_complete_from_direct_upload'
          : 'audio_upload_complete_from_live_recording',
        await getOrganisationId()
      )

      const audio_duration_seconds = await getMediaDurationSeconds(file)

      const transcriptionData = await createTranscription({
        body: {
          recording_id: recordingData.id,
          title,
          audio_duration_seconds,
        },
        signal,
      })

      recordAnalyticsEvent(
        isFile
          ? 'transcript_requested_for_direct_upload'
          : 'transcript_requested_for_live_recording'
      )

      if (recordingId) {
        await removeRecording(recordingId)
      }

      return transcriptionData.id
    },
    [
      createRecording,
      createTranscription,
      getOrganisationId,
      removeRecording,
      uploadBlob,
    ]
  )

  const form = useForm<TranscriptionForm>({
    defaultValues: {
      file: null,
      recordingId: undefined,
      title: '',
      ...defaultValues,
    },
  })

  return {
    isPending: isCreating || isConfirming || isUploading,
    onSubmit,
    form,
  }
}
