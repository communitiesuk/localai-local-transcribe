import { LegacyNav } from '@/components/layout/legacy-nav'
import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn() }),
}))

vi.mock('@/hooks/use-lock-navigation-context', () => ({
  useLockNavigationContext: () => ({
    lockNavigation: false,
    setLockNavigation: vi.fn(),
  }),
}))

describe('<LegacyNav />', () => {
  it('renders the three Lucide-icon nav buttons in order: Home, Templates, Settings', () => {
    render(<LegacyNav />)
    const buttons = screen.getAllByRole('link')
    expect(buttons.map((button) => button.textContent?.trim())).toEqual([
      'Home',
      'Templates',
      'Settings',
    ])
  })

  it('points each nav button at its current route', () => {
    render(<LegacyNav />)
    expect(screen.getByRole('link', { name: /home/i })).toHaveAttribute(
      'href',
      '/',
    )
    expect(screen.getByRole('link', { name: /templates/i })).toHaveAttribute(
      'href',
      '/templates',
    )
    expect(screen.getByRole('link', { name: /settings/i })).toHaveAttribute(
      'href',
      '/settings',
    )
  })
})
