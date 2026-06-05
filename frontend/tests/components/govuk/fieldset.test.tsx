import { GovukFieldset } from '@/components/govuk/fieldset'
import { render } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

describe('<GovukFieldset />', () => {
  it('renders a fieldset with the canonical govuk-fieldset class', () => {
    const { container } = render(
      <GovukFieldset>
        <span>child</span>
      </GovukFieldset>
    )
    const root = container.firstElementChild as HTMLElement
    expect(root.tagName).toBe('FIELDSET')
    expect(root).toHaveClass('govuk-fieldset')
  })

  it('wires describedBy onto aria-describedby', () => {
    const { container } = render(
      <GovukFieldset describedBy="hint-id error-id">
        <span>child</span>
      </GovukFieldset>
    )
    const root = container.firstElementChild as HTMLElement
    expect(root).toHaveAttribute('aria-describedby', 'hint-id error-id')
  })

  it('omits aria-describedby when describedBy is not provided', () => {
    const { container } = render(
      <GovukFieldset>
        <span>child</span>
      </GovukFieldset>
    )
    const root = container.firstElementChild as HTMLElement
    expect(root).not.toHaveAttribute('aria-describedby')
  })

  it('composes a caller-supplied className without clobbering the canonical class', () => {
    const { container } = render(
      <GovukFieldset className="mt-4">
        <span>child</span>
      </GovukFieldset>
    )
    const root = container.firstElementChild as HTMLElement
    expect(root).toHaveClass('govuk-fieldset', 'mt-4')
  })

  it('renders children inside the fieldset', () => {
    const { getByText } = render(
      <GovukFieldset>
        <span>inner</span>
      </GovukFieldset>
    )
    expect(getByText('inner')).toBeInTheDocument()
  })

  it('forwards arbitrary HTML attributes via spread', () => {
    const { getByTestId } = render(
      <GovukFieldset data-testid="fs">
        <span>child</span>
      </GovukFieldset>
    )
    expect(getByTestId('fs')).toBeInTheDocument()
  })
})
