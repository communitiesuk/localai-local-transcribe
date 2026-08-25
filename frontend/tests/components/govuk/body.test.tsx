import { GovukBody } from '@/components/govuk/body'
import { render } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

describe('<GovukBody />', () => {
  it('renders a <p> with the canonical govuk-body class by default', () => {
    const { container } = render(<GovukBody>Body text</GovukBody>)
    const root = container.firstElementChild as HTMLElement

    expect(root.tagName).toBe('P')
    expect(root).toHaveClass('govuk-body')
  })

  it('renders the large body class when size is "l"', () => {
    const { container } = render(
      <GovukBody size="l">Large body text</GovukBody>
    )
    const root = container.firstElementChild as HTMLElement

    expect(root).toHaveClass('govuk-body-l')
  })

  it('renders the small body class when size is "s"', () => {
    const { container } = render(
      <GovukBody size="s">Small body text</GovukBody>
    )
    const root = container.firstElementChild as HTMLElement

    expect(root).toHaveClass('govuk-body-s')
  })

  it('composes a caller-supplied className without clobbering the canonical class', () => {
    const { container } = render(
      <GovukBody className="mt-2">Body text</GovukBody>
    )
    const root = container.firstElementChild as HTMLElement

    expect(root).toHaveClass('govuk-body', 'mt-2')
  })

  it('forwards arbitrary HTML attributes via spread', () => {
    const { getByTestId } = render(
      <GovukBody data-testid="body" aria-live="polite">
        Body text
      </GovukBody>
    )

    expect(getByTestId('body')).toHaveAttribute('aria-live', 'polite')
  })

  it('renders children', () => {
    const { getByText } = render(<GovukBody>Inner text</GovukBody>)

    expect(getByText('Inner text')).toBeInTheDocument()
  })
})
