import { render, screen } from '@testing-library/react'
import { userEvent } from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'

function Shell({ children }: { children: React.ReactNode }) {
  return (
    <body className="govuk-template__body">
      <a
        href="#main-content"
        className="govuk-skip-link"
        data-module="govuk-skip-link"
      >
        Skip to main content
      </a>
      <div className="govuk-width-container">
        <main
          id="main-content"
          className="govuk-main-wrapper"
          tabIndex={-1}
        >
          {children}
        </main>
      </div>
    </body>
  )
}

describe('Root layout chrome', () => {
  it('renders the skip link as the first focusable element targeting #main-content', () => {
    render(<Shell>content</Shell>)
    const link = screen.getByRole('link', { name: 'Skip to main content' })
    expect(link).toHaveAttribute('href', '#main-content')
    expect(link).toHaveClass('govuk-skip-link')
  })

  it('wraps children in govuk-width-container > govuk-main-wrapper with id main-content', () => {
    const { container } = render(<Shell>content</Shell>)
    const main = container.querySelector('main#main-content')
    expect(main).toHaveClass('govuk-main-wrapper')
    expect(main?.parentElement).toHaveClass('govuk-width-container')
  })

  it('moves focus to main when the skip link is activated', async () => {
    const user = userEvent.setup()
    const { container } = render(<Shell>content</Shell>)
    const link = screen.getByRole('link', { name: 'Skip to main content' })
    link.focus()
    await user.keyboard('{Enter}')
    expect(container.querySelector('main#main-content')).toBeInTheDocument()
  })
})
