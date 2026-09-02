import { act, render, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { useRouter } from 'next/navigation'
import TranscriptionLoadingPage from '@/app/new/uploading/page'
import { useUploadRecordingStore } from '@/stores/use-upload-recording-store'

vi.mock('next/navigation', () => ({
  useRouter: vi.fn(),
}))

const initialStoreState = useUploadRecordingStore.getState()

describe('TranscriptionLoadingPage', () => {
  const push = vi.fn()
  const replace = vi.fn()

  beforeEach(() => {
    vi.mocked(useRouter).mockReturnValue({
      push,
      replace,
    } as unknown as ReturnType<typeof useRouter>)
  })

  afterEach(() => {
    push.mockReset()
    replace.mockReset()
    useUploadRecordingStore.setState(initialStoreState, true)
  })

  it('redirects to the standalone add details page once the upload succeeds, without also redirecting home', async () => {
    useUploadRecordingStore.setState({
      status: 'pending',
      transcriptionId: null,
      uploadingFrom: 'upload',
      error: null,
    })

    render(<TranscriptionLoadingPage />)

    act(() => {
      useUploadRecordingStore.setState({
        status: 'success',
        transcriptionId: 'transcription-123',
        error: null,
      })
    })

    await waitFor(() => {
      expect(push).toHaveBeenCalledWith('/new/metadata/transcription-123')
    })

    expect(replace).not.toHaveBeenCalled()
  })

  it('redirects home immediately if there is no upload in progress', () => {
    useUploadRecordingStore.setState({
      status: 'idle',
      transcriptionId: null,
      uploadingFrom: null,
      error: null,
    })

    render(<TranscriptionLoadingPage />)

    expect(replace).toHaveBeenCalledWith('/')
    expect(push).not.toHaveBeenCalled()
  })
})
