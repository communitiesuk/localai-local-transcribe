import GovFooter from '@/components/layout/footer'
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

describe('<GovFooter />', () => {
  it('renders a contentinfo landmark with the canonical govuk-footer class', () => {
    render(<GovFooter />)
    const footer = screen.getByRole('contentinfo')
    expect(footer).toHaveClass('govuk-footer')
  })

  it('contains the MHCLG logo as a decorative SVG', () => {
    const { container } = render(<GovFooter />)
    const svg = container.querySelector('.govuk-footer svg')
    expect(svg).not.toBeNull()
    expect(svg?.getAttribute('aria-hidden')).toBe('true')
  })

  it('renders the Privacy, Support, and Accessibility footer links', () => {
    render(<GovFooter />)
    expect(screen.getByRole('link', { name: 'Privacy' })).toHaveAttribute(
      'href',
      '/privacy'
    )
    expect(screen.getByRole('link', { name: 'Support' })).toHaveAttribute(
      'href',
      '/support'
    )
    expect(screen.getByRole('link', { name: 'Accessibility' })).toHaveAttribute(
      'href',
      '/accessibility'
    )
  })

  it('renders the Open Government Licence link in the meta section', () => {
    render(<GovFooter />)
    const ogl = screen.getByRole('link', { name: /Open Government Licence/i })
    expect(ogl).toHaveAttribute(
      'href',
      'https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/'
    )
    expect(ogl).toHaveAttribute('rel', 'license')
  })

  it('renders the Crown copyright link', () => {
    render(<GovFooter />)
    const crown = screen.getByRole('link', { name: /Crown copyright/i })
    expect(crown).toHaveClass('govuk-footer__copyright-logo')
  })
})
