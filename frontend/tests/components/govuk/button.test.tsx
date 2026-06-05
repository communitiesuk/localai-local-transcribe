import { GovukButton } from '@/components/govuk/button'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

describe('<GovukButton />', () => {
  it('renders <button type="submit"> with canonical class and data-module', () => {
    render(<GovukButton>Save</GovukButton>)
    const button = screen.getByRole('button', { name: 'Save' })
    expect(button.tagName).toBe('BUTTON')
    expect(button).toHaveAttribute('type', 'submit')
    expect(button).toHaveClass('govuk-button')
    expect(button).toHaveAttribute('data-module', 'govuk-button')
  })

  it.each([
    ['primary', undefined],
    ['secondary', 'govuk-button--secondary'],
    ['warning', 'govuk-button--warning'],
    ['inverse', 'govuk-button--inverse'],
  ] as const)('variant=%s applies the right modifier class', (variant, modifier) => {
    render(<GovukButton variant={variant}>Save</GovukButton>)
    const button = screen.getByRole('button', { name: 'Save' })
    expect(button).toHaveClass('govuk-button')
    if (modifier) {
      expect(button).toHaveClass(modifier)
    } else {
      expect(button.className.split(' ')).not.toContain(
        'govuk-button--secondary'
      )
    }
  })

  it('applies disabled + aria-disabled when disabled prop is true', () => {
    render(<GovukButton disabled>Save</GovukButton>)
    const button = screen.getByRole('button', { name: 'Save' })
    expect(button).toBeDisabled()
    expect(button).toHaveAttribute('aria-disabled', 'true')
  })

  it('when isSubmitting, renders loadingText, disables, and adds aria-disabled', () => {
    render(<GovukButton isSubmitting>Save</GovukButton>)
    const button = screen.getByRole('button', { name: 'Saving…' })
    expect(button).toBeDisabled()
    expect(button).toHaveAttribute('aria-disabled', 'true')
    expect(button).toHaveTextContent('Saving…')
  })

  it('allows a custom loadingText', () => {
    render(
      <GovukButton isSubmitting loadingText="Working…">
        Save
      </GovukButton>
    )
    expect(screen.getByRole('button', { name: 'Working…' })).toBeInTheDocument()
  })

  it('adds data-prevent-double-click when preventDoubleClick is true', () => {
    render(<GovukButton preventDoubleClick>Save</GovukButton>)
    expect(screen.getByRole('button', { name: 'Save' })).toHaveAttribute(
      'data-prevent-double-click',
      'true'
    )
  })

  it('omits data-prevent-double-click when not set', () => {
    render(<GovukButton>Save</GovukButton>)
    expect(screen.getByRole('button', { name: 'Save' })).not.toHaveAttribute(
      'data-prevent-double-click'
    )
  })

  it('renders the link variant as <a href role="button" draggable={false}> with canonical class', () => {
    render(<GovukButton href="/next">Continue</GovukButton>)
    const link = screen.getByRole('button', { name: 'Continue' })
    expect(link.tagName).toBe('A')
    expect(link).toHaveAttribute('href', '/next')
    expect(link).toHaveAttribute('draggable', 'false')
    expect(link).toHaveClass('govuk-button')
    expect(link).toHaveAttribute('data-module', 'govuk-button')
  })

  it('isStartButton adds the start modifier and renders the start icon', () => {
    const { container } = render(
      <GovukButton isStartButton>Start now</GovukButton>
    )
    const button = screen.getByRole('button', { name: /Start now/ })
    expect(button).toHaveClass('govuk-button--start')
    expect(container.querySelector('svg.govuk-button__start-icon')).not.toBeNull()
  })

  it('invokes onClick when clicked (button variant)', async () => {
    const onClick = vi.fn()
    render(
      <GovukButton type="button" onClick={onClick}>
        Click me
      </GovukButton>
    )
    await userEvent.click(screen.getByRole('button', { name: 'Click me' }))
    expect(onClick).toHaveBeenCalledTimes(1)
  })

  it('composes a caller className without clobbering canonical', () => {
    render(<GovukButton className="mt-4">Save</GovukButton>)
    const button = screen.getByRole('button', { name: 'Save' })
    expect(button).toHaveClass('govuk-button', 'mt-4')
  })

  it('regression — isSubmitting toggle re-enables and restores children', () => {
    const { rerender } = render(
      <GovukButton type="button" isSubmitting={false}>
        Save
      </GovukButton>
    )
    let button = screen.getByRole('button')
    expect(button).toBeEnabled()
    expect(button).toHaveTextContent('Save')

    rerender(
      <GovukButton type="button" isSubmitting>
        Save
      </GovukButton>
    )
    button = screen.getByRole('button')
    expect(button).toBeDisabled()
    expect(button).toHaveTextContent('Saving…')

    rerender(
      <GovukButton type="button" isSubmitting={false}>
        Save
      </GovukButton>
    )
    button = screen.getByRole('button')
    expect(button).toBeEnabled()
    expect(button).toHaveTextContent('Save')
  })

  it('regression — caller spread cannot clobber canonical data-module or className', () => {
    const hostile = { 'data-module': 'evil', className: 'bad' } as Record<
      string,
      string
    >
    render(<GovukButton {...hostile}>Save</GovukButton>)
    const button = screen.getByRole('button', { name: 'Save' })
    expect(button).toHaveAttribute('data-module', 'govuk-button')
    expect(button).toHaveClass('govuk-button')
  })
})
