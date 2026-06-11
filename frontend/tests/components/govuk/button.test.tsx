import { GovukButton, GovukButtonLink } from '@/components/govuk/button'
import { GovukLoadingButton } from '@/components/govuk/loading-button'
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
  ] as const)(
    'variant=%s applies the right modifier class',
    (variant, modifier) => {
      render(<GovukButton variant={variant}>Save</GovukButton>)
      const button = screen.getByRole('button', { name: 'Save' })
      expect(button).toHaveClass('govuk-button')
      if (modifier) {
        expect(button).toHaveClass(modifier)
      }

      const otherModifiers = [
        'govuk-button--secondary',
        'govuk-button--warning',
        'govuk-button--inverse',
      ].filter((m) => m !== modifier)

      otherModifiers.forEach((m) => {
        expect(button.className.split(' ')).not.toContain(m)
      })
    }
  )

  it('applies disabled when disabled prop is true', () => {
    render(<GovukButton disabled>Save</GovukButton>)
    const button = screen.getByRole('button', { name: 'Save' })
    expect(button).toBeDisabled()
    expect(button).not.toHaveAttribute('aria-disabled')
  })

  it('when isSubmitting, renders loadingText and disables', () => {
    render(<GovukLoadingButton isSubmitting>Save</GovukLoadingButton>)
    const button = screen.getByRole('button', { name: 'Saving…' })
    expect(button).toBeDisabled()
    expect(button).not.toHaveAttribute('aria-disabled')
    expect(button).toHaveTextContent('Saving…')
  })

  it('allows a custom loadingText', () => {
    render(
      <GovukLoadingButton isSubmitting loadingText="Working…">
        Save
      </GovukLoadingButton>
    )
    expect(screen.getByRole('button', { name: 'Working…' })).toBeInTheDocument()
  })



  it('renders the link variant as <a href role="button" draggable={false}> with canonical class', () => {
    render(<GovukButtonLink href="/next">Continue</GovukButtonLink>)
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
    expect(
      container.querySelector('svg.govuk-button__start-icon')
    ).not.toBeNull()
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
      <GovukLoadingButton type="button" isSubmitting={false}>
        Save
      </GovukLoadingButton>
    )
    let button = screen.getByRole('button')
    expect(button).toBeEnabled()
    expect(button).toHaveTextContent('Save')

    rerender(
      <GovukLoadingButton type="button" isSubmitting>
        Save
      </GovukLoadingButton>
    )
    button = screen.getByRole('button')
    expect(button).toBeDisabled()
    expect(button).toHaveTextContent('Saving…')

    rerender(
      <GovukLoadingButton type="button" isSubmitting={false}>
        Save
      </GovukLoadingButton>
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
