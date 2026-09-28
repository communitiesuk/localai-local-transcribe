import { render, screen, fireEvent } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { ModalConfirmationInterstitial } from '@/components/govuk/modal-confirmation-interstitial'

const defaultProps = {
  title: 'Discard changes?',
  body: 'If you continue, your changes will not be saved.',
  confirmLabel: 'Discard changes',
  onConfirm: vi.fn(),
  onCancel: vi.fn(),
}

describe('<ModalConfirmationInterstitial />', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the title as a heading', () => {
    render(<ModalConfirmationInterstitial {...defaultProps} />)
    expect(
      screen.getByRole('heading', { name: 'Discard changes?' })
    ).toBeInTheDocument()
  })

  it('renders the body text', () => {
    render(<ModalConfirmationInterstitial {...defaultProps} />)
    expect(
      screen.getByText('If you continue, your changes will not be saved.')
    ).toBeInTheDocument()
  })

  it('renders the confirm button with the provided label', () => {
    render(<ModalConfirmationInterstitial {...defaultProps} />)
    expect(
      screen.getByRole('button', { name: 'Discard changes' })
    ).toBeInTheDocument()
  })

  it('renders the cancel button with the default label', () => {
    render(<ModalConfirmationInterstitial {...defaultProps} />)
    expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument()
  })

  it('renders a custom cancel label when provided', () => {
    render(
      <ModalConfirmationInterstitial {...defaultProps} cancelLabel="Go back" />
    )
    expect(screen.getByRole('button', { name: 'Go back' })).toBeInTheDocument()
  })

  it('calls onConfirm when the confirm button is clicked', () => {
    render(<ModalConfirmationInterstitial {...defaultProps} />)
    fireEvent.click(screen.getByRole('button', { name: 'Discard changes' }))
    expect(defaultProps.onConfirm).toHaveBeenCalledOnce()
  })

  it('calls onCancel when the cancel button is clicked', () => {
    render(<ModalConfirmationInterstitial {...defaultProps} />)
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))
    expect(defaultProps.onCancel).toHaveBeenCalledOnce()
  })

  it('renders using the GOVUK warning classes when isWarning is true', () => {
    render(<ModalConfirmationInterstitial {...defaultProps} isWarning={true} />)

    const bodyText = screen.getByText(
      'If you continue, your changes will not be saved.'
    )
    const warningIcon = screen.getByText('!')

    expect(bodyText).toBeInTheDocument()
    expect(bodyText).toHaveClass('govuk-warning-text__text')
    expect(warningIcon).toBeInTheDocument()
    expect(warningIcon).toHaveClass('govuk-warning-text__icon')
  })

  it('renders without using the GOVUK warning classes when isWarning is false', () => {
    render(
      <ModalConfirmationInterstitial {...defaultProps} isWarning={false} />
    )

    const bodyText = screen.getByText(
      'If you continue, your changes will not be saved.'
    )
    const warningIcon = screen.queryByText('!')

    expect(bodyText).toBeInTheDocument()
    expect(bodyText).not.toHaveClass('govuk-warning-text__text')
    expect(warningIcon).not.toBeInTheDocument()
  })
})
