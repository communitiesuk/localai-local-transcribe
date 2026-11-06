import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { ConfirmationInterstitial } from '@/components/confirmation-interstitial'

vi.mock('next/navigation', () => ({
  useRouter: () => ({ back: vi.fn() }),
}))

const defaultProps = {
  title: 'Are you sure you want to create this template?',
  actionLabel: 'Create template',
  onAction: vi.fn(),
  cancelHref: '/templates/new',
}

describe('<ConfirmationInterstitial />', () => {
  it('renders the confirmation when the action is not pending', () => {
    render(
      <ConfirmationInterstitial {...defaultProps}>
        <p className="govuk-body">You will be able to use this template.</p>
      </ConfirmationInterstitial>
    )

    expect(
      screen.getByRole('heading', {
        name: 'Are you sure you want to create this template?',
      })
    ).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: 'Create template' })
    ).toBeEnabled()
    expect(screen.getByRole('link', { name: 'Cancel' })).toBeInTheDocument()
  })

  it('replaces the confirmation with the pending message while the action is pending', () => {
    render(
      <ConfirmationInterstitial
        {...defaultProps}
        actionPending
        pendingLabel="Creating template"
      >
        <p className="govuk-body">You will be able to use this template.</p>
      </ConfirmationInterstitial>
    )

    expect(screen.getByText('Creating template…')).toBeInTheDocument()
    expect(screen.queryByRole('heading')).not.toBeInTheDocument()
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })

  it('announces the pending state', () => {
    render(
      <ConfirmationInterstitial
        {...defaultProps}
        actionPending
        pendingLabel="Creating template"
      >
        <p className="govuk-body">You will be able to use this template.</p>
      </ConfirmationInterstitial>
    )

    expect(
      screen.getByRole('status', { name: 'Creating template' })
    ).toBeInTheDocument()
  })
})
