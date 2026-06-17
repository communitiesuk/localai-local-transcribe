import { GovukWarningText } from '@/components/govuk/warning'
import { render } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

describe('<GovukWarningText />', () => {
  it('renders a warning container with the canonical govuk-warning-text class', () => {
    const { container } = render(
      <GovukWarningText>Danger ahead</GovukWarningText>
    )

    const root = container.firstElementChild as HTMLElement

    expect(root.tagName).toBe('DIV')
    expect(root).toHaveClass('govuk-warning-text')
  })

  it('composes a caller-supplied className whilst preserving the GDS class', () => {
    const { container } = render(
      <GovukWarningText className="mt-4">Danger ahead</GovukWarningText>
    )

    const root = container.firstElementChild as HTMLElement

    expect(root).toHaveClass('govuk-warning-text', 'mt-4')
  })

  it('renders the warning icon', () => {
    const { container } = render(
      <GovukWarningText>Danger ahead</GovukWarningText>
    )

    const icon = container.querySelector(
      '.govuk-warning-text__icon'
    ) as HTMLElement

    expect(icon).toBeInTheDocument()
    expect(icon).toHaveTextContent('!')
    expect(icon).toHaveAttribute('aria-hidden', 'true')
  })

  it('renders visually hidden warning label', () => {
    const { container } = render(
      <GovukWarningText>Danger ahead</GovukWarningText>
    )

    const hidden = container.querySelector('.govuk-visually-hidden')

    expect(hidden).toBeInTheDocument()
    expect(hidden).toHaveTextContent('Warning')
  })

  it('renders children inside the warning text element', () => {
    const { getByText } = render(
      <GovukWarningText>Danger ahead</GovukWarningText>
    )

    expect(getByText('Danger ahead')).toBeInTheDocument()
  })

  it('forwards arbitrary HTML attributes via spread', () => {
    const { getByTestId } = render(
      <GovukWarningText data-testid="warning">Danger ahead</GovukWarningText>
    )

    expect(getByTestId('warning')).toBeInTheDocument()
  })
})
