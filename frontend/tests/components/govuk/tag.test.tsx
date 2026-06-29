import { GovukTag } from '@/components/govuk/tag'
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

describe('<GovukTag />', () => {
  it('renders a <strong> element with the canonical govuk-tag class', () => {
    const { container } = render(<GovukTag>Alpha</GovukTag>)
    const root = container.firstElementChild as HTMLElement
    expect(root.tagName).toBe('STRONG')
    expect(root).toHaveClass('govuk-tag')
  })

  it('renders text content', () => {
    render(<GovukTag>Beta</GovukTag>)
    expect(screen.getByText('Beta')).toBeInTheDocument()
  })

  it('applies no colour modifier when colour is omitted', () => {
    const { container } = render(<GovukTag>Default</GovukTag>)
    const root = container.firstElementChild as HTMLElement
    expect(root.className).toBe('govuk-tag')
  })

  it.each([
    'grey',
    'green',
    'turquoise',
    'blue',
    'light-blue',
    'purple',
    'pink',
    'red',
    'orange',
    'yellow',
  ] as const)('applies the govuk-tag--%s modifier class', (colour) => {
    const { container } = render(<GovukTag colour={colour}>Label</GovukTag>)
    const root = container.firstElementChild as HTMLElement
    expect(root).toHaveClass('govuk-tag', `govuk-tag--${colour}`)
  })

  it('composes a caller-supplied className without clobbering the canonical class', () => {
    const { container } = render(
      <GovukTag className="govuk-!-margin-bottom-2">Label</GovukTag>
    )
    const root = container.firstElementChild as HTMLElement
    expect(root).toHaveClass('govuk-tag', 'govuk-!-margin-bottom-2')
  })

  it('forwards arbitrary HTML attributes via spread', () => {
    render(<GovukTag data-testid="status-tag">Active</GovukTag>)
    expect(screen.getByTestId('status-tag')).toBeInTheDocument()
  })
})
