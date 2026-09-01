import type { TranscriptionForm } from '@/hooks/use-start-transcription'
import { create } from 'zustand'

type UploadRecordingStatus = 'idle' | 'pending' | 'success' | 'error'
type UploadingFrom = 'upload' | 'recording' | null

type UploadRecordingStore = {
  status: UploadRecordingStatus
  transcriptionId: string | null
  uploadingFrom: UploadingFrom
  error: string | null
  startUpload: (
    uploadingFrom: UploadingFrom,
    values: TranscriptionForm,
    submit: (values: TranscriptionForm) => Promise<string | null>
  ) => Promise<void>
  reset: () => void
}

export const useUploadRecordingStore = create<UploadRecordingStore>((set) => ({
  status: 'idle',
  transcriptionId: null,
  uploadingFrom: null,
  error: null,

  startUpload: async (uploadingFrom, values, submit) => {
    set({
      status: 'pending',
      transcriptionId: null,
      uploadingFrom,
      error: null,
    })

    try {
      const transcriptionId = await submit(values)

      set({
        status: 'success',
        transcriptionId,
        error: null,
      })
    } catch (error) {
      set({
        status: 'error',
        transcriptionId: null,
        error:
          error instanceof Error ? error.message : 'Failed to upload recording',
      })
    }
  },

  reset: () => {
    set({
      status: 'idle',
      transcriptionId: null,
      uploadingFrom: null,
      error: null,
    })
  },
}))
