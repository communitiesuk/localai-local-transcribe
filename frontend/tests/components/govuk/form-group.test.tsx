import { GovukFormGroup } from '@/components/govuk/form-group'
import { render } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

describe('<GovukFormGroup />', () => {
  it('renders a div with the canonical govuk-form-group class', () => {
    const { container } = render(
      <GovukFormGroup>
        <span>child</span>
      </GovukFormGroup>
    )
    const root = container.firstElementChild as HTMLElement
    expect(root.tagName).toBe('DIV')
    expect(root).toHaveClass('govuk-form-group')
  })

  it('adds govuk-form-group--error when hasError is true', () => {
    const { container } = render(
      <GovukFormGroup hasError>
        <span>child</span>
      </GovukFormGroup>
    )
    const root = container.firstElementChild as HTMLElement
    expect(root).toHaveClass('govuk-form-group', 'govuk-form-group--error')
  })

  it('does not add the error modifier when hasError is false or omitted', () => {
    const { container } = render(
      <GovukFormGroup>
        <span>child</span>
      </GovukFormGroup>
    )
    const root = container.firstElementChild as HTMLElement
    expect(root).not.toHaveClass('govuk-form-group--error')
  })

  it('composes a caller-supplied className without clobbering the canonical class', () => {
    const { container } = render(
      <GovukFormGroup className="mt-4">
        <span>child</span>
      </GovukFormGroup>
    )
    const root = container.firstElementChild as HTMLElement
    expect(root).toHaveClass('govuk-form-group', 'mt-4')
  })

  it('forwards arbitrary HTML attributes via spread', () => {
    const { getByTestId } = render(
      <GovukFormGroup data-testid="fg" aria-label="form group">
        <span>child</span>
      </GovukFormGroup>
    )
    const root = getByTestId('fg')
    expect(root).toHaveAttribute('aria-label', 'form group')
  })

  it('renders children inside the group', () => {
    const { getByText } = render(
      <GovukFormGroup>
        <span>inner</span>
      </GovukFormGroup>
    )
    expect(getByText('inner')).toBeInTheDocument()
  })
})
