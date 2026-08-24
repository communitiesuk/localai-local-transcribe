import {
  createRecordingRecordingsPostMutation,
  createTranscriptionOnlyTranscriptionsOnlyPostMutation,
} from '@/lib/client/@tanstack/react-query.gen'
import { getFileExtension } from '@/lib/getFileExtension'
import { useRecordingDb } from '@/providers/transcription-db-provider'
import { useMutation } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { useCallback } from 'react'
import { useBannerStore } from '@/stores/use-banner-store'
import { useForm } from 'react-hook-form'

export type TranscriptionOnlyForm = {
  file: Blob | File | null
  recordingId?: string
  title?: string
}

export const useStartTranscriptionOnly = () => {
  const router = useRouter()
  const setBanner = useBannerStore((store) => store.setBanner)
  const { removeRecording } = useRecordingDb()

  const { mutateAsync: createTranscriptionOnly, isPending: isCreating } =
    useMutation({
      ...createTranscriptionOnlyTranscriptionsOnlyPostMutation(),
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
    async ({ file, recordingId, title }: TranscriptionOnlyForm) => {
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
        body: { file_extension, file_created_at },
      })

      await uploadBlob({
        file,
        uploadUrl: recordingData.upload_url,
      })

      const transcriptionData = await createTranscriptionOnly({
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
    [createRecording, createTranscriptionOnly, removeRecording, uploadBlob]
  )

  const form = useForm<TranscriptionOnlyForm>({
    defaultValues: {
      file: null,
      title: '',
    },
  })

  return {
    isPending: isCreating || isConfirming || isUploading,
    onSubmit,
    form,
  }
}
