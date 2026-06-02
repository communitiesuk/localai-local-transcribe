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

  it('defaults to width 32 and height 30 (matches the pre-extraction sizing)', () => {
    const { container } = render(<MhclgLogo />)
    const svg = getSvg(container)
    expect(svg.getAttribute('width')).toBe('32')
    expect(svg.getAttribute('height')).toBe('30')
  })

  it('accepts width / height / className overrides', () => {
    const { container } = render(
      <MhclgLogo width={64} height={60} className="custom-class" />
    )
    const svg = getSvg(container)
    expect(svg.getAttribute('width')).toBe('64')
    expect(svg.getAttribute('height')).toBe('60')
    expect(svg).toHaveClass('custom-class')
  })

  it('renders the 7 brand dots and the wreath path', () => {
    const { container } = render(<MhclgLogo />)
    const svg = getSvg(container)
    expect(svg.querySelectorAll('circle')).toHaveLength(7)
    expect(svg.querySelectorAll('path')).toHaveLength(1)
  })
})
