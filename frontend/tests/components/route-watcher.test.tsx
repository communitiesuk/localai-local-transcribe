import { render } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { RouteWatcher } from '@/components/route-watcher'
import { useUploadRecordingStore } from '@/stores/use-upload-recording-store'

let mockPathname = '/new/record/in-person'

vi.mock('next/navigation', () => ({
  usePathname: () => mockPathname,
}))

const initialStoreState = useUploadRecordingStore.getState()

describe('<RouteWatcher />', () => {
  beforeEach(() => {
    mockPathname = '/new/record/in-person'
  })

  afterEach(() => {
    useUploadRecordingStore.setState(initialStoreState, true)
  })

  it('does not call handleRouteChange on mount, or when re-rendered with an unchanged pathname (simulates React Strict Mode)', () => {
    const handleRouteChange = vi.fn()
    useUploadRecordingStore.setState({ handleRouteChange })

    const { rerender } = render(<RouteWatcher />)
    rerender(<RouteWatcher />)

    expect(handleRouteChange).not.toHaveBeenCalled()
  })

  it('calls handleRouteChange when the pathname genuinely changes', () => {
    const handleRouteChange = vi.fn()
    useUploadRecordingStore.setState({ handleRouteChange })

    const { rerender } = render(<RouteWatcher />)

    mockPathname = '/'
    rerender(<RouteWatcher />)

    expect(handleRouteChange).toHaveBeenCalledTimes(1)
  })
})
