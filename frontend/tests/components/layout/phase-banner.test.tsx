import { PhaseBanner } from '@/components/layout/phase-banner'
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

describe('<PhaseBanner />', () => {
  it('renders canonical govuk-phase-banner markup with a govuk-tag for Alpha', () => {
    const { container } = render(<PhaseBanner />)
    expect(container.querySelector('.govuk-phase-banner')).toBeInTheDocument()
    expect(
      container.querySelector('.govuk-phase-banner__content')
    ).toBeInTheDocument()
    const tag = screen.getByText('Alpha')
    expect(tag).toHaveClass('govuk-tag', 'govuk-phase-banner__content__tag')
    expect(tag.tagName).toBe('STRONG')
  })

  it('places the supporting text inside govuk-phase-banner__text', () => {
    const { container } = render(<PhaseBanner />)
    const text = container.querySelector('.govuk-phase-banner__text')
    expect(text?.textContent).toContain('This is a new service')
  })
})
