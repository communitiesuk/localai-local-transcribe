import { act, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { useRouter } from 'next/navigation'
import { UploadStatus } from '@/components/audio/upload-status'
import { LockNavigationProvider } from '@/hooks/use-lock-navigation-context'
import { useUploadRecordingStore } from '@/stores/use-upload-recording-store'

vi.mock('next/navigation', () => ({
  useRouter: vi.fn(),
}))

const initialStoreState = useUploadRecordingStore.getState()

const setOnline = (online: boolean) => {
  Object.defineProperty(window.navigator, 'onLine', {
    configurable: true,
    value: online,
  })
}

const fireBeforeUnload = () => {
  const event = new Event('beforeunload', { cancelable: true })
  window.dispatchEvent(event)
  return event.defaultPrevented
}

describe('UploadStatus', () => {
  const push = vi.fn()

  beforeEach(() => {
    vi.mocked(useRouter).mockReturnValue({
      push,
    } as unknown as ReturnType<typeof useRouter>)
  })

  afterEach(() => {
    push.mockReset()
    useUploadRecordingStore.setState(initialStoreState, true)
    setOnline(true)
  })

  it('shows a processing spinner while the upload is pending and not awaiting manual retry', () => {
    useUploadRecordingStore.setState({
      status: 'pending',
      uploadingFrom: 'recording',
      awaitingManualRetry: false,
    })

    render(<UploadStatus />)

    expect(screen.getByRole('status')).toBeInTheDocument()
    expect(screen.getByText('Processing recording…')).toBeInTheDocument()
  })

  it('shows the error view with an enabled retry button when online and the upload failed', () => {
    setOnline(true)
    useUploadRecordingStore.setState({
      status: 'error',
      error: 'Something broke',
    })

    render(<UploadStatus />)

    expect(
      screen.getByText('We could not upload your recording')
    ).toBeInTheDocument()
    expect(screen.getByRole('alert')).toHaveTextContent(
      'Something went wrong while uploading your recording'
    )
    expect(screen.getByRole('button', { name: 'Retry' })).toBeEnabled()
  })

  it('disables the retry button while offline in the error view', () => {
    setOnline(false)
    useUploadRecordingStore.setState({
      status: 'error',
      error: 'Something broke',
    })

    render(<UploadStatus />)

    expect(screen.getByRole('button', { name: 'Retry' })).toBeDisabled()
  })

  it('shows a "waiting to reconnect" message and a disabled retry button when offline and awaiting manual retry', () => {
    setOnline(false)
    useUploadRecordingStore.setState({
      status: 'pending',
      awaitingManualRetry: true,
    })

    render(<UploadStatus />)

    expect(screen.getByText('Waiting to reconnect')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Retry' })).toBeDisabled()
  })

  it('shows a "ready to retry" message and an enabled retry button once back online while awaiting manual retry', () => {
    setOnline(true)
    useUploadRecordingStore.setState({
      status: 'pending',
      awaitingManualRetry: true,
    })

    render(<UploadStatus />)

    expect(screen.getByText('Ready to retry')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Retry' })).toBeEnabled()
  })

  it('calls retryUpload when the retry button is clicked', async () => {
    const user = userEvent.setup()
    const retryUpload = vi.fn()
    setOnline(true)
    useUploadRecordingStore.setState({
      status: 'error',
      error: 'Something broke',
      retryUpload,
    })

    render(<UploadStatus />)

    await user.click(screen.getByRole('button', { name: 'Retry' }))

    expect(retryUpload).toHaveBeenCalledTimes(1)
  })

  it('redirects to the metadata page and resets the store once the upload succeeds', async () => {
    const reset = vi.fn()
    useUploadRecordingStore.setState({
      status: 'pending',
      uploadingFrom: 'upload',
    })

    render(<UploadStatus />)

    act(() => {
      useUploadRecordingStore.setState({
        status: 'success',
        transcriptionId: 'transcription-789',
        reset,
      })
    })

    await waitFor(() => {
      expect(push).toHaveBeenCalledWith('/new/metadata/transcription-789')
    })
    expect(reset).toHaveBeenCalledTimes(1)
  })

  it('warns before leaving the site while the upload is pending', () => {
    useUploadRecordingStore.setState({
      status: 'pending',
      uploadingFrom: 'recording',
    })

    render(<UploadStatus />, { wrapper: LockNavigationProvider })

    expect(fireBeforeUnload()).toBe(true)
  })

  it('warns before leaving the site when the upload has failed', () => {
    useUploadRecordingStore.setState({
      status: 'error',
      error: 'Something broke',
    })

    render(<UploadStatus />, { wrapper: LockNavigationProvider })

    expect(fireBeforeUnload()).toBe(true)
  })

  it('stops warning before leaving the site once the upload succeeds', () => {
    useUploadRecordingStore.setState({
      status: 'pending',
      uploadingFrom: 'recording',
    })

    render(<UploadStatus />, { wrapper: LockNavigationProvider })

    act(() => {
      useUploadRecordingStore.setState({
        status: 'success',
        transcriptionId: 'transcription-789',
        reset: vi.fn(),
      })
    })

    expect(fireBeforeUnload()).toBe(false)
  })
})
