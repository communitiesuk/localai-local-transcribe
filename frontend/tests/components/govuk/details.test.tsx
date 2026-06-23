import { GovukDetails } from '@/components/govuk/details'
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

describe('<GovukDetails />', () => {
  it('renders a details element with the canonical class and data-module', () => {
    const { container } = render(
      <GovukDetails summary="More about approved domains">
        <p>Body text</p>
      </GovukDetails>
    )
    const root = container.firstElementChild as HTMLElement
    expect(root.tagName).toBe('DETAILS')
    expect(root).toHaveClass('govuk-details')
    expect(root).toHaveAttribute('data-module', 'govuk-details')
  })

  it('renders the summary text inside the canonical summary markup', () => {
    render(
      <GovukDetails summary="More about approved domains">
        <p>Body text</p>
      </GovukDetails>
    )
    const summary = screen.getByText('More about approved domains')
    expect(summary.tagName).toBe('SPAN')
    expect(summary).toHaveClass('govuk-details__summary-text')
    expect(summary.parentElement).toHaveClass('govuk-details__summary')
  })

  it('renders children inside the canonical text wrapper', () => {
    const { container } = render(
      <GovukDetails summary="Help">
        <p>Some explanatory text</p>
      </GovukDetails>
    )
    const text = container.querySelector('.govuk-details__text') as HTMLElement
    expect(text).not.toBeNull()
    expect(text.textContent).toBe('Some explanatory text')
  })

  it('is closed by default and opens when the open prop is set', () => {
    const { container, rerender } = render(
      <GovukDetails summary="Help">
        <p>Body</p>
      </GovukDetails>
    )
    const root = container.querySelector('details') as HTMLDetailsElement
    expect(root.open).toBe(false)

    rerender(
      <GovukDetails summary="Help" open>
        <p>Body</p>
      </GovukDetails>
    )
    expect(
      (container.querySelector('details') as HTMLDetailsElement).open
    ).toBe(true)
  })

  it('composes a caller-supplied className without clobbering the canonical class', () => {
    const { container } = render(
      <GovukDetails summary="Help" className="mt-4">
        <p>Body</p>
      </GovukDetails>
    )
    const root = container.firstElementChild as HTMLElement
    expect(root).toHaveClass('govuk-details', 'mt-4')
  })

  it('forwards arbitrary HTML attributes via spread', () => {
    render(
      <GovukDetails summary="Help" data-testid="domains-help">
        <p>Body</p>
      </GovukDetails>
    )
    expect(screen.getByTestId('domains-help')).toBeInTheDocument()
  })
})
