import { render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, beforeEach, vi } from 'vitest'
import { BannerNotification } from '@/components/banner-notification'
import { useBannerStore } from '@/stores/use-banner-store'

let pathname = '/user-management'

vi.mock('next/navigation', () => ({
  usePathname: () => pathname,
}))

describe('<BannerNotification />', () => {
  beforeEach(() => {
    pathname = '/user-management'
    useBannerStore.getState().clearBanner()
    Element.prototype.scrollIntoView = vi.fn()
  })

  it('keeps a banner available across remounts', () => {
    useBannerStore.getState().setBanner({
      variant: 'success',
      title: 'Approved domains updated',
      message: 'Successfully updated approved domains',
    })

    const { unmount } = render(<BannerNotification />)
    expect(screen.getByText('Approved domains updated')).toBeInTheDocument()

    unmount()
    render(<BannerNotification />)

    expect(screen.getByText('Approved domains updated')).toBeInTheDocument()
    expect(
      screen.getByText('Successfully updated approved domains')
    ).toBeInTheDocument()
  })

  it('clears a banner after navigating away from the path that displayed it', async () => {
    useBannerStore.getState().setBanner({
      variant: 'success',
      title: 'Approved domains updated',
      message: 'Successfully updated approved domains',
    })

    const { unmount } = render(<BannerNotification />)
    expect(screen.getByText('Approved domains updated')).toBeInTheDocument()

    unmount()
    pathname = '/templates'
    render(<BannerNotification />)

    expect(
      screen.queryByText('Approved domains updated')
    ).not.toBeInTheDocument()
    await waitFor(() => {
      expect(useBannerStore.getState().banner).toBeNull()
    })
  })
})
