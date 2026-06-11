import { GovukErrorSummary } from '@/components/govuk/error-summary'
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

describe('<GovukErrorSummary />', () => {
  it('renders the canonical root with govuk-error-summary class and data-module', () => {
    const { container } = render(
      <GovukErrorSummary errorList={[{ text: 'A failed' }]} />
    )
    const root = container.querySelector('.govuk-error-summary') as HTMLElement
    expect(root).not.toBeNull()
    expect(root).toHaveAttribute('data-module', 'govuk-error-summary')
  })

  it('renders an inner <div role="alert"> wrapping the title and body', () => {
    const { container } = render(
      <GovukErrorSummary errorList={[{ text: 'A failed' }]} />
    )
    const alert = container.querySelector(
      '.govuk-error-summary > div[role="alert"]'
    )
    expect(alert).not.toBeNull()
    expect(
      container.querySelector(
        '.govuk-error-summary div[role="alert"] .govuk-error-summary__title'
      )
    ).not.toBeNull()
    expect(
      container.querySelector(
        '.govuk-error-summary div[role="alert"] .govuk-error-summary__body'
      )
    ).not.toBeNull()
  })

  it('defaults the title to "There is a problem"', () => {
    render(<GovukErrorSummary errorList={[{ text: 'A failed' }]} />)
    expect(screen.getByText('There is a problem')).toBeInTheDocument()
  })

  it('uses a custom title when supplied', () => {
    render(
      <GovukErrorSummary
        title="Sort this out"
        errorList={[{ text: 'A failed' }]}
      />
    )
    expect(screen.getByText('Sort this out')).toBeInTheDocument()
  })

  it('renders linked <li><a>...</a></li> rows when errorList items carry href', () => {
    render(
      <GovukErrorSummary
        errorList={[
          { href: '#a', text: 'Field A invalid' },
          { href: '#b', text: 'Field B invalid' },
        ]}
      />
    )
    const linkA = screen.getByRole('link', { name: 'Field A invalid' })
    expect(linkA).toHaveAttribute('href', '#a')
    const linkB = screen.getByRole('link', { name: 'Field B invalid' })
    expect(linkB).toHaveAttribute('href', '#b')
  })

  it('renders plain <li> rows when errorList items have no href', () => {
    const { container } = render(
      <GovukErrorSummary
        errorList={[{ text: 'Field A invalid' }, { text: 'Field B invalid' }]}
      />
    )
    expect(container.querySelectorAll('a').length).toBe(0)
    const items = container.querySelectorAll('.govuk-error-summary__list > li')
    expect(items).toHaveLength(2)
    expect(items[0].textContent).toBe('Field A invalid')
  })

  it('renders the description as a <p> inside the body before the list', () => {
    const { container } = render(
      <GovukErrorSummary
        description="Please fix the errors below."
        errorList={[{ text: 'A failed' }]}
      />
    )
    const body = container.querySelector(
      '.govuk-error-summary__body'
    ) as HTMLElement
    const first = body.firstElementChild as HTMLElement
    expect(first.tagName).toBe('P')
    expect(first.textContent).toBe('Please fix the errors below.')
  })

  it('regression — caller cannot clobber the canonical data-module or className via rest', () => {
    const hostile = { 'data-module': 'evil' } as Record<string, string>
    const { container } = render(
      <GovukErrorSummary
        {...hostile}
        className="mt-2"
        errorList={[{ text: 'A failed' }]}
      />
    )
    const root = container.querySelector('.govuk-error-summary') as HTMLElement
    expect(root).toHaveAttribute('data-module', 'govuk-error-summary')
    expect(root).toHaveClass('govuk-error-summary', 'mt-2')
  })

  it('composes a caller className without clobbering the canonical class', () => {
    const { container } = render(
      <GovukErrorSummary className="mb-4" errorList={[{ text: 'A failed' }]} />
    )
    const root = container.querySelector('.govuk-error-summary') as HTMLElement
    expect(root).toHaveClass('govuk-error-summary', 'mb-4')
  })
})
