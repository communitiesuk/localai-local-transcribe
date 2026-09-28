import { render, screen } from '@testing-library/react'
import { describe, expect, it, beforeEach, vi } from 'vitest'
import { BannerNotification } from '@/components/banner-notification'
import { useBannerStore } from '@/stores/use-banner-store'

describe('<BannerNotification />', () => {
  beforeEach(() => {
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
})
