import { GovukNotificationBanner } from '@/components/govuk/notification-banner'
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

describe('<GovukNotificationBanner />', () => {
  it('renders a div with the canonical govuk-notification-banner class and data-module', () => {
    const { container } = render(
      <GovukNotificationBanner>
        <p>Message</p>
      </GovukNotificationBanner>
    )
    const root = container.firstElementChild as HTMLElement
    expect(root.tagName).toBe('DIV')
    expect(root).toHaveClass('govuk-notification-banner')
    expect(root).toHaveAttribute('data-module', 'govuk-notification-banner')
  })

  it('important variant (default): role is "region" and title is "Important"', () => {
    render(
      <GovukNotificationBanner>
        <p>Message</p>
      </GovukNotificationBanner>
    )
    const banner = screen.getByRole('region')
    expect(banner).toBeInTheDocument()
    expect(screen.getByText('Important')).toBeInTheDocument()
  })

  it('important variant does not carry the success modifier class', () => {
    const { container } = render(
      <GovukNotificationBanner>
        <p>Message</p>
      </GovukNotificationBanner>
    )
    expect(container.firstElementChild).not.toHaveClass(
      'govuk-notification-banner--success'
    )
  })

  it('success variant: role is "alert" and has the success modifier class', () => {
    const { container } = render(
      <GovukNotificationBanner variant="success">
        <p>Done</p>
      </GovukNotificationBanner>
    )
    const root = container.firstElementChild as HTMLElement
    expect(root).toHaveAttribute('role', 'alert')
    expect(root).toHaveClass('govuk-notification-banner--success')
  })

  it('success variant title is "Success" by default', () => {
    render(
      <GovukNotificationBanner variant="success">
        <p>Done</p>
      </GovukNotificationBanner>
    )
    expect(screen.getByText('Success')).toBeInTheDocument()
  })

  it('aria-labelledby on the banner references the title element id', () => {
    const { container } = render(
      <GovukNotificationBanner titleId="banner-title">
        <p>Message</p>
      </GovukNotificationBanner>
    )
    const root = container.firstElementChild as HTMLElement
    expect(root).toHaveAttribute('aria-labelledby', 'banner-title')
    expect(container.querySelector('#banner-title')).not.toBeNull()
  })

  it('uses the default titleId when none is supplied', () => {
    const { container } = render(
      <GovukNotificationBanner>
        <p>Message</p>
      </GovukNotificationBanner>
    )
    const root = container.firstElementChild as HTMLElement
    expect(root).toHaveAttribute(
      'aria-labelledby',
      'govuk-notification-banner-title'
    )
    expect(
      container.querySelector('#govuk-notification-banner-title')
    ).not.toBeNull()
  })

  it('renders a custom title when the title prop is supplied', () => {
    render(
      <GovukNotificationBanner title="Notice">
        <p>Message</p>
      </GovukNotificationBanner>
    )
    expect(screen.getByText('Notice')).toBeInTheDocument()
  })

  it('renders children inside the content wrapper', () => {
    const { container } = render(
      <GovukNotificationBanner>
        <p>Body text here</p>
      </GovukNotificationBanner>
    )
    const content = container.querySelector(
      '.govuk-notification-banner__content'
    ) as HTMLElement
    expect(content.textContent).toBe('Body text here')
  })

  it('composes a caller-supplied className without clobbering the canonical class', () => {
    const { container } = render(
      <GovukNotificationBanner className="govuk-!-margin-bottom-4">
        <p>Message</p>
      </GovukNotificationBanner>
    )
    expect(container.firstElementChild).toHaveClass(
      'govuk-notification-banner',
      'govuk-!-margin-bottom-4'
    )
  })

  it('forwards arbitrary HTML attributes via spread', () => {
    render(
      <GovukNotificationBanner data-testid="my-banner">
        <p>Message</p>
      </GovukNotificationBanner>
    )
    expect(screen.getByTestId('my-banner')).toBeInTheDocument()
  })
})
