import { GovukHint } from '@/components/govuk/hint'
import { render } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

describe('<GovukHint />', () => {
  it('renders a div with the canonical govuk-hint class', () => {
    const { container } = render(<GovukHint>Helpful note</GovukHint>)
    const root = container.firstElementChild as HTMLElement
    expect(root.tagName).toBe('DIV')
    expect(root).toHaveClass('govuk-hint')
  })

  it('lands an id on the rendered element when provided', () => {
    const { container } = render(
      <GovukHint id="dob-hint">Day month year</GovukHint>
    )
    const root = container.firstElementChild as HTMLElement
    expect(root).toHaveAttribute('id', 'dob-hint')
  })

  it('composes a caller-supplied className without clobbering the canonical class', () => {
    const { container } = render(
      <GovukHint className="mt-1">Helpful note</GovukHint>
    )
    const root = container.firstElementChild as HTMLElement
    expect(root).toHaveClass('govuk-hint', 'mt-1')
  })

  it('forwards arbitrary HTML attributes via spread', () => {
    const { getByTestId } = render(
      <GovukHint data-testid="hint" aria-live="polite">
        Helpful note
      </GovukHint>
    )
    expect(getByTestId('hint')).toHaveAttribute('aria-live', 'polite')
  })

  it('renders children', () => {
    const { getByText } = render(<GovukHint>Inner text</GovukHint>)
    expect(getByText('Inner text')).toBeInTheDocument()
  })
})
