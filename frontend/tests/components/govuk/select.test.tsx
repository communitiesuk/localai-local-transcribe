import { GovukSelect } from '@/components/govuk/select'
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

describe('<GovukSelect />', () => {
  it('renders a <select> with the govuk-select class and the given id', () => {
    const { container } = render(
      <GovukSelect id="sort">
        <option value="newest">Newest</option>
      </GovukSelect>
    )
    const root = container.firstElementChild as HTMLElement
    expect(root.tagName).toBe('SELECT')
    expect(root).toHaveClass('govuk-select')
    expect(root).toHaveAttribute('id', 'sort')
  })

  it('renders its option children', () => {
    render(
      <GovukSelect id="sort">
        <option value="newest">Newest</option>
        <option value="oldest">Oldest</option>
      </GovukSelect>
    )
    expect(screen.getByRole('option', { name: 'Newest' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'Oldest' })).toBeInTheDocument()
  })

  it('applies the error modifier when aria-invalid is true', () => {
    const { container } = render(
      <GovukSelect id="sort" aria-invalid>
        <option value="newest">Newest</option>
      </GovukSelect>
    )
    expect(container.firstElementChild).toHaveClass('govuk-select--error')
  })
})
