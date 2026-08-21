import { GovukSectionBreak } from '@/components/govuk/section-break'
import { render } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

describe('<GovukSectionBreak />', () => {
  it('renders an <hr> with the canonical govuk-section-break class', () => {
    const { container } = render(<GovukSectionBreak />)
    const root = container.firstElementChild as HTMLElement

    expect(root.tagName).toBe('HR')
    expect(root).toHaveClass('govuk-section-break')
  })

  it('adds govuk-section-break--visible by default', () => {
    const { container } = render(<GovukSectionBreak />)
    const root = container.firstElementChild as HTMLElement

    expect(root).toHaveClass('govuk-section-break--visible')
  })

  it('does not add govuk-section-break--visible when visible is false', () => {
    const { container } = render(<GovukSectionBreak visible={false} />)
    const root = container.firstElementChild as HTMLElement

    expect(root).not.toHaveClass('govuk-section-break--visible')
  })

  it.each([
    ['xl', 'govuk-section-break--xl'],
    ['l', 'govuk-section-break--l'],
    ['m', 'govuk-section-break--m'],
  ] as const)(
    'renders the %s section break class',
    (size, expectedSizeClassName) => {
      const { container } = render(<GovukSectionBreak size={size} />)
      const root = container.firstElementChild as HTMLElement

      expect(root).toHaveClass(
        'govuk-section-break',
        expectedSizeClassName,
        'govuk-section-break--visible'
      )
    }
  )

  it('composes a caller-supplied className without clobbering the canonical class', () => {
    const { container } = render(<GovukSectionBreak className="mt-2" />)
    const root = container.firstElementChild as HTMLElement

    expect(root).toHaveClass('govuk-section-break', 'mt-2')
  })

  it('forwards arbitrary HTML attributes via spread', () => {
    const { getByTestId } = render(
      <GovukSectionBreak data-testid="section-break" aria-hidden="true" />
    )

    expect(getByTestId('section-break')).toHaveAttribute('aria-hidden', 'true')
  })
})
