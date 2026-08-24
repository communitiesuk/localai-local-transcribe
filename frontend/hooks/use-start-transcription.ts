import {
  createRecordingRecordingsPostMutation,
  createTranscriptionTranscriptionsPostMutation,
} from '@/lib/client/@tanstack/react-query.gen'
import { getFileExtension } from '@/lib/getFileExtension'
import { useRecordingDb } from '@/providers/transcription-db-provider'
import { useMutation } from '@tanstack/react-query'
import { useCallback } from 'react'
import { useForm } from 'react-hook-form'

export type TranscriptionForm = {
  file: Blob | File | null
  recordingId?: string
  title?: string
}

export const useStartTranscription = (
  defaultValues?: Partial<TranscriptionForm>
) => {
  const { removeRecording } = useRecordingDb()

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
    }: {
      uploadUrl: string
      file: Blob | File
    }) => {
      const uploadResponse = await fetch(uploadUrl, {
        method: 'PUT',
        body: file,
        headers: {
          'x-ms-blob-type': 'BlockBlob',
        },
      })

      if (!uploadResponse.ok) {
        throw new Error('Failed to upload file')
      }
    },
  })

  const onSubmit = useCallback(
    async ({ file, recordingId, title }: TranscriptionForm) => {
      if (!file) {
        return null
      }

      const isFile = file instanceof File

      const file_extension = isFile ? getFileExtension(file.name) : 'webm'

      const recordingData = await createRecording({
        body: { file_extension },
      })

      await uploadBlob({
        file,
        uploadUrl: recordingData.upload_url,
      })

      const transcriptionData = await createTranscription({
        body: {
          recording_id: recordingData.id,
          title,
        },
      })

      if (recordingId) {
        await removeRecording(recordingId)
      }

      return transcriptionData.id
    },
    [createRecording, createTranscription, removeRecording, uploadBlob]
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
