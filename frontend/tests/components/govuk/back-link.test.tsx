import { GovukBackLink } from '@/components/govuk/back-link'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

const mockBack = vi.fn()
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    back: mockBack,
  }),
}))

describe('<GovukBackLink />', () => {
  it('renders an <a> with the canonical govuk-back-link class and provided href', () => {
    render(<GovukBackLink href="/previous">Back</GovukBackLink>)
    const link = screen.getByRole('link', { name: 'Back' })
    expect(link.tagName).toBe('A')
    expect(link).toHaveClass('govuk-back-link')
    expect(link).toHaveAttribute('href', '/previous')
  })

  it('defaults the href to "#" and triggers router.back() when clicked without href', async () => {
    render(<GovukBackLink />)
    const link = screen.getByRole('link', { name: 'Back' })
    expect(link).toHaveAttribute('href', '#')

    mockBack.mockClear()
    await userEvent.click(link)
    expect(mockBack).toHaveBeenCalledTimes(1)
  })

  it('calls custom onClick handler if provided', async () => {
    const onClick = vi.fn()
    render(<GovukBackLink onClick={onClick} />)
    const link = screen.getByRole('link', { name: 'Back' })

    mockBack.mockClear()
    await userEvent.click(link)
    expect(onClick).toHaveBeenCalledTimes(1)
    expect(mockBack).not.toHaveBeenCalled()
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
