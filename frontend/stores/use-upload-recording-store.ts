import type { TranscriptionForm } from '@/hooks/use-start-transcription'
import { create } from 'zustand'

type UploadRecordingStatus = 'idle' | 'pending' | 'success' | 'error'

type UploadRecordingStore = {
  status: UploadRecordingStatus
  transcriptionId: string | null
  error: string | null
  startUpload: (
    values: TranscriptionForm,
    submit: (values: TranscriptionForm) => Promise<string | null>
  ) => Promise<void>
  reset: () => void
}

export const useUploadRecordingStore = create<UploadRecordingStore>((set) => ({
  status: 'idle',
  transcriptionId: null,
  error: null,

  startUpload: async (values, submit) => {
    set({
      status: 'pending',
      transcriptionId: null,
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
      error: null,
    })
  },
}))
