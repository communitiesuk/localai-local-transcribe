import { GovukLink } from '@/components/govuk/link'
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

describe('<GovukLink />', () => {
  it('renders an anchor with the canonical govuk-link class', () => {
    render(<GovukLink href="#">HTML example</GovukLink>)

    const link = screen.getByRole('link', { name: 'HTML example' })

    expect(link.tagName).toBe('A')
    expect(link).toHaveClass('govuk-link')
  })

  it('adds href onto the rendered anchor', () => {
    render(<GovukLink href="/example">HTML example</GovukLink>)

    expect(screen.getByRole('link')).toHaveAttribute('href', '/example')
  })

  it('composes a caller-supplied className without clobbering the canonical class', () => {
    render(
      <GovukLink href="#" className="mt-2">
        HTML example
      </GovukLink>
    )

    expect(screen.getByRole('link')).toHaveClass('govuk-link', 'mt-2')
  })

  it('forwards arbitrary HTML attributes via spread', () => {
    render(
      <GovukLink href="#" data-testid="link" aria-label="View HTML example">
        HTML example
      </GovukLink>
    )

    expect(screen.getByTestId('link')).toHaveAttribute('data-testid', 'link')
  })
})
