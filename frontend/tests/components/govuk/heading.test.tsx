import { GovukHeading } from '@/components/govuk/heading'
import { render } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

describe('<GovukHeading />', () => {
  it('renders an h1 by default with the canonical govuk-heading-l class', () => {
    const { container } = render(<GovukHeading>Title</GovukHeading>)

    const root = container.firstElementChild as HTMLElement

    expect(root.tagName).toBe('H1')
    expect(root).toHaveClass('govuk-heading-l')
  })

  it('renders the requested heading size', () => {
    const { container } = render(<GovukHeading size="xl">Title</GovukHeading>)

    const root = container.firstElementChild as HTMLElement

    expect(root).toHaveClass('govuk-heading-xl')
  })

  it('renders the requested heading tag', () => {
    const { container } = render(<GovukHeading as="h3">Title</GovukHeading>)

    const root = container.firstElementChild as HTMLElement

    expect(root.tagName).toBe('H3')
    expect(root).toHaveClass('govuk-heading-l')
  })

  it('composes a caller-supplied className whilst preserving the GDS class', () => {
    const { container } = render(
      <GovukHeading className="mt-4">Title</GovukHeading>
    )

    const root = container.firstElementChild as HTMLElement

    expect(root).toHaveClass('govuk-heading-l', 'mt-4')
  })

  it('renders children inside the heading', () => {
    const { getByText } = render(
      <GovukHeading>
        <span>Inner content</span>
      </GovukHeading>
    )

    expect(getByText('Inner content')).toBeInTheDocument()
  })

  it('forwards arbitrary HTML attributes via spread', () => {
    const { getByTestId } = render(
      <GovukHeading data-testid="heading">Title</GovukHeading>
    )

    expect(getByTestId('heading')).toBeInTheDocument()
  })
})
