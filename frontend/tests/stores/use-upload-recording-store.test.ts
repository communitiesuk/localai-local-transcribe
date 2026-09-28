import { afterEach, describe, expect, it, vi } from 'vitest'
import { useUploadRecordingStore } from '@/stores/use-upload-recording-store'

const initialStoreState = useUploadRecordingStore.getState()

const setOnline = (online: boolean) => {
  Object.defineProperty(window.navigator, 'onLine', {
    configurable: true,
    value: online,
  })
}

describe('useUploadRecordingStore', () => {
  afterEach(() => {
    useUploadRecordingStore.setState(initialStoreState, true)
    setOnline(true)
    vi.restoreAllMocks()
  })

  it('uploads immediately and reports success when online', async () => {
    const submit = vi.fn().mockResolvedValue('transcription-123')

    await useUploadRecordingStore
      .getState()
      .startUpload('recording', { file: null }, submit)

    expect(submit).toHaveBeenCalledWith({ file: null })
    expect(useUploadRecordingStore.getState()).toMatchObject({
      status: 'success',
      transcriptionId: 'transcription-123',
      error: null,
      awaitingManualRetry: false,
    })
  })

  it('sets an error status and retains the values/submit fn when the submit fn rejects', async () => {
    const submit = vi.fn().mockRejectedValue(new Error('boom'))

    await useUploadRecordingStore
      .getState()
      .startUpload('upload', { file: null }, submit)

    expect(useUploadRecordingStore.getState()).toMatchObject({
      status: 'error',
      transcriptionId: null,
      error: 'boom',
      awaitingManualRetry: false,
    })
  })

  it('does not call submit and instead awaits manual retry when starting an upload while offline', async () => {
    setOnline(false)
    const submit = vi.fn().mockResolvedValue('transcription-123')

    await useUploadRecordingStore
      .getState()
      .startUpload('recording', { file: null }, submit)

    expect(submit).not.toHaveBeenCalled()
    expect(useUploadRecordingStore.getState()).toMatchObject({
      status: 'pending',
      awaitingManualRetry: true,
    })
  })

  it('retryUpload re-runs the retained submit fn with the retained values and succeeds', async () => {
    const submit = vi.fn().mockResolvedValue('transcription-456')
    const file = new Blob(['audio'])

    setOnline(false)
    await useUploadRecordingStore
      .getState()
      .startUpload('recording', { file }, submit)
    expect(submit).not.toHaveBeenCalled()

    setOnline(true)
    await useUploadRecordingStore.getState().retryUpload()

    expect(submit).toHaveBeenCalledWith({ file })
    expect(useUploadRecordingStore.getState()).toMatchObject({
      status: 'success',
      transcriptionId: 'transcription-456',
    })
  })

  it('retryUpload is a no-op when there are no retained values/submit fn (e.g. nothing was ever started)', async () => {
    await useUploadRecordingStore.getState().retryUpload()

    expect(useUploadRecordingStore.getState()).toMatchObject({
      status: 'idle',
      transcriptionId: null,
      error: null,
    })
  })

  it('retryUpload can be called repeatedly and re-fails while the underlying error persists', async () => {
    const submit = vi.fn().mockRejectedValue(new Error('still broken'))

    await useUploadRecordingStore
      .getState()
      .startUpload('recording', { file: null }, submit)
    expect(useUploadRecordingStore.getState().status).toBe('error')

    await useUploadRecordingStore.getState().retryUpload()

    expect(submit).toHaveBeenCalledTimes(2)
    expect(useUploadRecordingStore.getState()).toMatchObject({
      status: 'error',
      error: 'still broken',
    })
  })

  it('reset clears status, retained values/submit fn and awaitingManualRetry', async () => {
    const submit = vi.fn().mockRejectedValue(new Error('boom'))
    await useUploadRecordingStore
      .getState()
      .startUpload('recording', { file: null }, submit)

    useUploadRecordingStore.getState().reset()

    expect(useUploadRecordingStore.getState()).toMatchObject({
      status: 'idle',
      transcriptionId: null,
      uploadingFrom: null,
      error: null,
      awaitingManualRetry: false,
      _values: null,
      _submit: null,
    })

    await useUploadRecordingStore.getState().retryUpload()
    expect(submit).toHaveBeenCalledTimes(1)
  })
})
