import { PhaseBanner } from '@/components/layout/phase-banner'
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

describe('<PhaseBanner />', () => {
  it('renders canonical govuk-phase-banner markup with a govuk-tag for Alpha', () => {
    const { container } = render(<PhaseBanner />)
    expect(container.querySelector('.govuk-phase-banner')).toBeInTheDocument()
    expect(
      container.querySelector('.govuk-phase-banner__content'),
    ).toBeInTheDocument()
    const tag = screen.getByText('Alpha')
    expect(tag).toHaveClass('govuk-tag', 'govuk-phase-banner__content__tag')
    expect(tag.tagName).toBe('STRONG')
  })

  it('places the supporting text inside govuk-phase-banner__text', () => {
    const { container } = render(<PhaseBanner />)
    const text = container.querySelector('.govuk-phase-banner__text')
    expect(text?.textContent).toContain('This is a new service')
    expect(text?.textContent).toContain('give your feedback')
  })

  it('preserves the feedback link to the current survey URL, open in a new tab', () => {
    render(<PhaseBanner />)
    const link = screen.getByRole('link', { name: 'give your feedback' })
    expect(link).toHaveAttribute(
      'href',
      'https://surveys.publishing.service.gov.uk/s/MAQMR1/',
    )
    expect(link).toHaveClass('govuk-link')
    expect(link).toHaveAttribute('target', '_blank')
    expect(link).toHaveAttribute('rel', 'noopener noreferrer')
  })
})
