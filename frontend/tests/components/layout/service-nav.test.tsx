import { render, screen, fireEvent } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { ServiceNav } from '@/components/layout/service-nav'

let mockPathname = '/'
const mockPush = vi.fn()
let mockLockNavigation: string | boolean = false
const mockSetLockNavigation = vi.fn()
let mockUserRoles: string[] | undefined = []

vi.mock('next/navigation', () => ({
  usePathname: () => mockPathname,
  useRouter: () => ({
    push: mockPush,
  }),
}))

vi.mock('@/hooks/use-lock-navigation-context', () => ({
  useLockNavigationContext: () => ({
    lockNavigation: mockLockNavigation,
    setLockNavigation: mockSetLockNavigation,
  }),
}))

vi.mock('@tanstack/react-query', () => ({
  useQuery: () => ({
    data: {
      roles: mockUserRoles,
    },
  }),
}))

vi.mock('@/lib/client/@tanstack/react-query.gen', () => ({
  getUserUsersMeGetOptions: vi.fn(() => ({})),
}))

describe('<ServiceNav />', () => {
  beforeEach(() => {
    mockPathname = '/'
    mockLockNavigation = false
    mockUserRoles = []
    vi.clearAllMocks()
  })

  it('renders standard govuk-service-navigation structure', () => {
    const { container } = render(<ServiceNav />)
    const outer = container.querySelector('section.govuk-service-navigation')
    expect(outer).not.toBeNull()
    expect(outer).toHaveAttribute('data-module', 'govuk-service-navigation')
    expect(outer?.querySelector('.govuk-width-container')).not.toBeNull()
    expect(
      outer?.querySelector('.govuk-service-navigation__container')
    ).not.toBeNull()
    expect(
      outer?.querySelector('.govuk-service-navigation__service-name')
    ).not.toBeNull()
    expect(
      outer?.querySelector('nav.govuk-service-navigation__wrapper')
    ).not.toBeNull()
  })

  it('renders the service name Local Transcribe linking to /', () => {
    render(<ServiceNav />)
    const serviceLink = screen.getByRole('link', { name: 'Local Transcribe' })
    expect(serviceLink).toHaveAttribute('href', '/')
    expect(serviceLink).toHaveClass('govuk-service-navigation__link')
  })

  it('renders items Home, My recordings, Templates, Settings for non-admin users', () => {
    mockUserRoles = ['standard_user']
    render(<ServiceNav />)
    const links = screen.getAllByRole('link')
    const linkTexts = links.map((link) => link.textContent?.trim())
    expect(linkTexts).toEqual([
      'Local Transcribe',
      'Home',
      'My recordings',
      'Templates',
      'Settings',
    ])
  })

  it('renders User management for admin users', () => {
    mockUserRoles = ['local_authority_admin']
    render(<ServiceNav />)
    const links = screen.getAllByRole('link')
    const linkTexts = links.map((link) => link.textContent?.trim())
    expect(linkTexts).toEqual([
      'Local Transcribe',
      'Home',
      'My recordings',
      'Templates',
      'Settings',
      'User management',
    ])
  })

  it('correctly sets active state for Home on exact / pathname', () => {
    mockPathname = '/'
    mockUserRoles = ['standard_user']
    render(<ServiceNav />)

    const homeLink = screen.getByRole('link', { name: 'Home' })
    const homeItem = homeLink.closest('.govuk-service-navigation__item')

    expect(homeItem).toHaveClass('govuk-service-navigation__item--active')
    expect(homeLink).toHaveAttribute('aria-current', 'page')
    expect(homeLink.querySelector('strong')).toHaveClass(
      'govuk-service-navigation__active-fallback'
    )
  })

  it('correctly sets active state for Home on /new and sub-routes', () => {
    mockPathname = '/new/upload'
    mockUserRoles = ['standard_user']
    render(<ServiceNav />)

    const homeLink = screen.getByRole('link', { name: 'Home' })
    const homeItem = homeLink.closest('.govuk-service-navigation__item')

    expect(homeItem).toHaveClass('govuk-service-navigation__item--active')
  })

  it('correctly sets active state for My recordings on /transcriptions and sub-routes', () => {
    mockPathname = '/transcriptions/abc-123'
    mockUserRoles = ['standard_user']
    render(<ServiceNav />)

    const recordingsLink = screen.getByRole('link', { name: 'My recordings' })
    const recordingsItem = recordingsLink.closest(
      '.govuk-service-navigation__item'
    )

    expect(recordingsItem).toHaveClass('govuk-service-navigation__item--active')
  })

  it('respects lockNavigation and blocks immediate routing, showing the warning dialog', async () => {
    mockPathname = '/'
    mockUserRoles = ['standard_user']
    mockLockNavigation = 'Warning: leaving page'
    render(<ServiceNav />)

    const templatesBtn = screen.getByRole('button', { name: 'Templates' })
    expect(templatesBtn).toBeInTheDocument()

    fireEvent.click(templatesBtn)

    expect(
      screen.getByText('Are you sure you want to leave the page?')
    ).toBeInTheDocument()
    expect(screen.getByText('Warning: leaving page')).toBeInTheDocument()
    const continueBtn = screen.getByRole('button', { name: 'Continue' })
    fireEvent.click(continueBtn)

    expect(mockSetLockNavigation).toHaveBeenCalledWith(false)
    expect(mockPush).toHaveBeenCalledWith('/templates')
  })
})
