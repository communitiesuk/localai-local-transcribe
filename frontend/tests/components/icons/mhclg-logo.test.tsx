import { MhclgLogo } from '@/components/icons/mhclg-logo'
import { render } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

const getSvg = (container: HTMLElement) => {
  const svg = container.querySelector('svg')
  if (!svg) throw new Error('MhclgLogo did not render an <svg>')
  return svg
}

describe('<MhclgLogo />', () => {
  it('renders an aria-hidden, focusable=false svg with the canonical viewBox', () => {
    const { container } = render(<MhclgLogo />)
    const svg = getSvg(container)
    expect(svg.getAttribute('aria-hidden')).toBe('true')
    expect(svg.getAttribute('focusable')).toBe('false')
    expect(svg.getAttribute('viewBox')).toBe('0 0 64 60')
  })

  it('ships at the canonical 32x30 size', () => {
    const { container } = render(<MhclgLogo />)
    const svg = getSvg(container)
    expect(svg.getAttribute('width')).toBe('32')
    expect(svg.getAttribute('height')).toBe('30')
  })

  it('accepts a className override (used by header for govuk-header__logotype)', () => {
    const { container } = render(
      <MhclgLogo className="govuk-header__logotype" />
    )
    const svg = getSvg(container)
    expect(svg).toHaveClass('govuk-header__logotype')
  })
})
