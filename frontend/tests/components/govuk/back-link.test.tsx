import { GovukBackLink } from '@/components/govuk/back-link'
import { GovukBackButton } from '@/components/govuk/back-button'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

describe('<GovukBackLink /> (server, href)', () => {
  it('renders an <a> with the canonical govuk-back-link class and provided href', () => {
    render(<GovukBackLink href="/previous">Back</GovukBackLink>)
    const link = screen.getByRole('link', { name: 'Back' })
    expect(link.tagName).toBe('A')
    expect(link).toHaveClass('govuk-back-link')
    expect(link).toHaveAttribute('href', '/previous')
  })

  it('defaults the text to "Back" when no children are provided', () => {
    render(<GovukBackLink href="/previous" />)
    const link = screen.getByRole('link', { name: 'Back' })
    expect(link).toBeInTheDocument()
  })

  it('renders custom children when provided', () => {
    render(<GovukBackLink href="/previous">Go back</GovukBackLink>)
    expect(screen.getByRole('link', { name: 'Go back' })).toBeInTheDocument()
  })

  it('adds govuk-back-link--inverse when inverse is true', () => {
    render(
      <GovukBackLink href="/previous" inverse>
        Back
      </GovukBackLink>
    )
    expect(screen.getByRole('link', { name: 'Back' })).toHaveClass(
      'govuk-back-link',
      'govuk-back-link--inverse'
    )
  })

  it('composes a caller-supplied className without clobbering the canonical class', () => {
    render(
      <GovukBackLink href="/previous" className="mt-2">
        Back
      </GovukBackLink>
    )
    expect(screen.getByRole('link', { name: 'Back' })).toHaveClass(
      'govuk-back-link',
      'mt-2'
    )
  })

  it('regression: spread cannot clobber the canonical className', () => {
    const hostile = { className: 'bad' } as Record<string, string>
    render(
      <GovukBackLink href="/x" {...hostile}>
        Back
      </GovukBackLink>
    )
    const link = screen.getByRole('link', { name: 'Back' })
    expect(link).toHaveClass('govuk-back-link')
  })
})

describe('<GovukBackButton /> (client, onClick)', () => {
  it('renders an <a href="#"> with the canonical govuk-back-link class', () => {
    render(<GovukBackButton onClick={() => undefined}>Back</GovukBackButton>)
    const link = screen.getByRole('link', { name: 'Back' })
    expect(link.tagName).toBe('A')
    expect(link).toHaveClass('govuk-back-link')
    expect(link).toHaveAttribute('href', '#')
  })

  it('calls onClick and prevents default navigation', async () => {
    const onClick = vi.fn((event: React.MouseEvent<HTMLAnchorElement>) => {
      expect(event.defaultPrevented).toBe(true)
    })
    render(<GovukBackButton onClick={onClick}>Back</GovukBackButton>)
    await userEvent.click(screen.getByRole('link', { name: 'Back' }))
    expect(onClick).toHaveBeenCalledTimes(1)
  })

  it('defaults the text to "Back" when no children are provided', () => {
    render(<GovukBackButton onClick={() => undefined} />)
    expect(screen.getByRole('link', { name: 'Back' })).toBeInTheDocument()
  })

  it('adds the inverse modifier when inverse is true', () => {
    render(
      <GovukBackButton onClick={() => undefined} inverse>
        Back
      </GovukBackButton>
    )
    expect(screen.getByRole('link', { name: 'Back' })).toHaveClass(
      'govuk-back-link--inverse'
    )
  })

  it('regression: spread cannot clobber the canonical className', () => {
    const hostile = { className: 'bad' } as Record<string, string>
    render(
      <GovukBackButton onClick={() => undefined} {...hostile}>
        Back
      </GovukBackButton>
    )
    expect(screen.getByRole('link', { name: 'Back' })).toHaveClass(
      'govuk-back-link'
    )
  })
})
