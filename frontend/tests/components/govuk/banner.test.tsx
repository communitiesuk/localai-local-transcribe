import { GovukNotificationBanner } from '@/components/govuk/banner'
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

describe('<GovukNotificationBanner />', () => {
  it('renders a div with the canonical class and data-module', () => {
    const { container } = render(
      <GovukNotificationBanner title="Important">
        <p>Body text</p>
      </GovukNotificationBanner>
    )

    const root = container.firstElementChild as HTMLElement
    expect(root.tagName).toBe('DIV')
    expect(root).toHaveClass('govuk-notification-banner')
    expect(root).toHaveAttribute('data-module', 'govuk-notification-banner')
  })

  it('renders the title inside the canonical heading markup', () => {
    render(
      <GovukNotificationBanner title="Important">
        <p>Body text</p>
      </GovukNotificationBanner>
    )

    const title = screen.getByText('Important')
    expect(title.tagName).toBe('H2')
    expect(title).toHaveClass('govuk-notification-banner__title')
  })

  it('renders children inside the content wrapper', () => {
    const { container } = render(
      <GovukNotificationBanner title="Important">
        <p>Some body content</p>
      </GovukNotificationBanner>
    )

    const content = container.querySelector(
      '.govuk-notification-banner__content'
    ) as HTMLElement

    expect(content).not.toBeNull()
    expect(content.textContent).toContain('Some body content')
  })

  it('applies success variant class and alert role when variant is success', () => {
    const { container } = render(
      <GovukNotificationBanner title="Success" variant="success">
        <p>Done</p>
      </GovukNotificationBanner>
    )

    const root = container.firstElementChild as HTMLElement

    expect(root).toHaveClass('govuk-notification-banner--success')
    expect(root).toHaveAttribute('role', 'alert')
  })

  it('uses region role by default', () => {
    const { container } = render(
      <GovukNotificationBanner title="Important">
        <p>Body</p>
      </GovukNotificationBanner>
    )

    const root = container.firstElementChild as HTMLElement
    expect(root).toHaveAttribute('role', 'region')
  })

  it('uses the provided titleId for aria-labelledby', () => {
    const { container } = render(
      <GovukNotificationBanner title="Important" titleId="custom-id">
        <p>Body</p>
      </GovukNotificationBanner>
    )

    const root = container.firstElementChild as HTMLElement
    expect(root).toHaveAttribute('aria-labelledby', 'custom-id')
  })

  it('composes a caller-supplied className without clobbering canonical class', () => {
    const { container } = render(
      <GovukNotificationBanner title="Important" className="mt-4">
        <p>Body</p>
      </GovukNotificationBanner>
    )

    const root = container.firstElementChild as HTMLElement
    expect(root).toHaveClass('govuk-notification-banner', 'mt-4')
  })

  it('forwards arbitrary HTML attributes via spread', () => {
    render(
      <GovukNotificationBanner title="Important" data-testid="banner">
        <p>Body</p>
      </GovukNotificationBanner>
    )

    expect(screen.getByTestId('banner')).toBeInTheDocument()
  })
})
