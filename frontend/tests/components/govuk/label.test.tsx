import { GovukLabel } from '@/components/govuk/label'
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

describe('<GovukLabel />', () => {
  it('renders a label with the canonical govuk-label class', () => {
    render(<GovukLabel>Name</GovukLabel>)
    const label = screen.getByText('Name')
    expect(label.tagName).toBe('LABEL')
    expect(label).toHaveClass('govuk-label')
  })

  it('wires htmlFor onto the rendered label', () => {
    render(<GovukLabel htmlFor="example">Name</GovukLabel>)
    const label = screen.getByText('Name')
    expect(label).toHaveAttribute('for', 'example')
  })

  it.each(['s', 'm', 'l', 'xl'] as const)(
    'adds govuk-label--%s when size=%s',
    (size) => {
      render(<GovukLabel size={size}>Name</GovukLabel>)
      const label = screen.getByText('Name')
      expect(label).toHaveClass('govuk-label', `govuk-label--${size}`)
    }
  )

  it('does not add a size modifier when size is omitted', () => {
    render(<GovukLabel>Name</GovukLabel>)
    const label = screen.getByText('Name')
    expect(label.className).toBe('govuk-label')
  })

  it('composes a caller-supplied className without clobbering the canonical class', () => {
    render(<GovukLabel className="mt-2">Name</GovukLabel>)
    const label = screen.getByText('Name')
    expect(label).toHaveClass('govuk-label', 'mt-2')
  })

  it('forwards arbitrary HTML attributes via spread', () => {
    render(
      <GovukLabel data-testid="lbl" aria-describedby="hint">
        Name
      </GovukLabel>
    )
    expect(screen.getByTestId('lbl')).toHaveAttribute(
      'aria-describedby',
      'hint'
    )
  })
})
