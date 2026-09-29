import type { TranscriptionForm } from '@/hooks/use-start-transcription'
import { create } from 'zustand'

type UploadRecordingStatus = 'idle' | 'pending' | 'success' | 'error'
type UploadingFrom = 'upload' | 'recording' | null
type SubmitFn = (
  values: TranscriptionForm,
  signal: AbortSignal
) => Promise<string | null>

type UploadRecordingStore = {
  status: UploadRecordingStatus
  transcriptionId: string | null
  uploadingFrom: UploadingFrom
  error: string | null

  awaitingManualRetry: boolean
  startUpload: (
    uploadingFrom: UploadingFrom,
    values: TranscriptionForm,
    submit: SubmitFn
  ) => Promise<void>

  retryUpload: () => Promise<void>
  cancelRequest: () => void
  reset: () => void
  _values: TranscriptionForm | null
  _submit: SubmitFn | null
}

export const useUploadRecordingStore = create<UploadRecordingStore>(
  (set, get) => {
    const isOnline = () =>
      typeof navigator === 'undefined' ? true : navigator.onLine

    let controller: AbortController | null = null

    const runUpload = async (
      uploadingFrom: UploadingFrom,
      values: TranscriptionForm,
      submit: SubmitFn
    ) => {
      const online = isOnline()

      controller?.abort()
      controller = new AbortController()
      const { signal } = controller

      set({
        status: 'pending',
        transcriptionId: null,
        uploadingFrom,
        error: null,
        _values: values,
        _submit: submit,
        awaitingManualRetry: !online,
      })

      if (!online) {
        return
      }

      try {
        const transcriptionId = await submit(values, signal)

        if (signal.aborted) {
          return
        }

        set({
          status: 'success',
          transcriptionId,
          error: null,
        })
      } catch (error) {
        if (
          signal.aborted ||
          (error instanceof Error && error.name === 'AbortError')
        ) {
          return
        }

        set({
          status: 'error',
          transcriptionId: null,
          error:
            error instanceof Error
              ? error.message
              : 'Failed to upload recording',
        })
      }
    }

    return {
      status: 'idle',
      transcriptionId: null,
      uploadingFrom: null,
      error: null,
      awaitingManualRetry: false,
      _values: null,
      _submit: null,

      startUpload: (uploadingFrom, values, submit) =>
        runUpload(uploadingFrom, values, submit),

      retryUpload: () => {
        const { uploadingFrom, _values, _submit } = get()
        if (!_values || !_submit) {
          return Promise.resolve()
        }
        return runUpload(uploadingFrom, _values, _submit)
      },

      cancelRequest: () => {
        controller?.abort()
        controller = null
      },

      reset: () => {
        get().cancelRequest()
        set({
          status: 'idle',
          transcriptionId: null,
          uploadingFrom: null,
          error: null,
          awaitingManualRetry: false,
          _values: null,
          _submit: null,
        })
      },
    }
  }
)
