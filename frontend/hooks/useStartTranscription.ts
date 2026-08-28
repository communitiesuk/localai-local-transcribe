import { TranscriptionForm } from '@/components/audio/types'
import {
  createRecordingRecordingsPostMutation,
  createTranscriptionOnlyTranscriptionsOnlyPostMutation,
  createTranscriptionTranscriptionsPostMutation,
} from '@/lib/client/@tanstack/react-query.gen'
import { getFileExtension } from '@/lib/getFileExtension'
import { useRecordingDb } from '@/providers/transcription-db-provider'
import { useMutation } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import posthog from 'posthog-js'
import { useCallback } from 'react'
import { useForm } from 'react-hook-form'

export const useStartTranscription = ({
  defaultValues,
  transcriptionOnly = false,
}: {
  defaultValues?: Partial<TranscriptionForm>
  transcriptionOnly?: boolean
} = {}) => {
  const router = useRouter()
  const { removeRecording } = useRecordingDb()
  const { mutateAsync: createTranscription, isPending: isCreating } =
    useMutation({
      ...createTranscriptionTranscriptionsPostMutation(),
    })
  const {
    mutateAsync: createTranscriptionOnly,
    isPending: isCreatingTranscriptionOnly,
  } = useMutation({
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
        throw new Error('Failed to upload file to S3')
      }
    },
  })

  const onSubmit = useCallback(
    async ({ file, template, agenda, recordingId }: TranscriptionForm) => {
      if (!file) {
        return
      }
      const isFile = file instanceof File
      const source = !!defaultValues?.recordingId
        ? 'offline-recording'
        : isFile
          ? 'upload'
          : 'recording'
      const file_extension = isFile ? getFileExtension(file.name) : 'webm'
      const file_created_at =
        isFile && file.lastModified
          ? new Date(file.lastModified).toISOString()
          : undefined
      posthog.capture('transcription_started', {
        file_type: file.type || '',
        source,
      })
      await createRecording(
        { body: { file_extension, file_created_at } },
        {
          onSuccess: async (recordingData) => {
            await uploadBlob(
              { file, uploadUrl: recordingData.upload_url },
              {
                onSuccess: async () => {
                  const transcriptionData = transcriptionOnly
                    ? await createTranscriptionOnly({
                        body: {
                          recording_id: recordingData.id,
                        },
                      })
                    : await createTranscription({
                        body: {
                          recording_id: recordingData.id,
                          template_id: template.id,
                          template_name: template.name,
                          agenda,
                        },
                      })
                  if (recordingId) {
                    await removeRecording(recordingId)
                  }
                  router.push(
                    transcriptionOnly
                      ? `/transcriptions/${transcriptionData.id}?details=open`
                      : `/transcriptions/${transcriptionData.id}`
                  )
                },
              }
            )
          },
        }
      )
    },
    [
      createRecording,
      createTranscription,
      createTranscriptionOnly,
      defaultValues?.recordingId,
      removeRecording,
      router,
      transcriptionOnly,
      uploadBlob,
    ]
  )
  const form = useForm<TranscriptionForm>({
    defaultValues: {
      file: null,
      template: { name: 'General', agenda_usage: 'optional' },
      ...defaultValues,
    },
  })
  return {
    isPending:
      isCreating || isCreatingTranscriptionOnly || isConfirming || isUploading,
    onSubmit,
    form,
  }
}
