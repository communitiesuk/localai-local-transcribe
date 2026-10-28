import { ReviewGuardModal } from '@/components/review-guard/review-guard-modal'
import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

describe('<ReviewGuardModal />', () => {
  it('does not render when closed', () => {
    render(
      <ReviewGuardModal
        open={false}
        onClose={vi.fn()}
        onConfirm={vi.fn()}
        action="copy"
        subject="transcript"
      />
    )

    expect(screen.queryByText('Confirm review')).not.toBeInTheDocument()
  })

  it('renders review warning and checkbox when open', () => {
    render(
      <ReviewGuardModal
        open
        onClose={vi.fn()}
        onConfirm={vi.fn()}
        action="download"
        subject="document"
      />
    )

    expect(screen.getByText('Confirm review')).toBeInTheDocument()
  })

  it('disables confirm until the checkbox is checked', () => {
    render(
      <ReviewGuardModal
        open
        onClose={vi.fn()}
        onConfirm={vi.fn()}
        action="copy"
        subject="transcript"
      />
    )

    const confirmButton = screen.getByRole('button', { name: 'Confirm' })
    expect(confirmButton).toBeDisabled()

    fireEvent.click(screen.getByLabelText("I've reviewed the transcript"))
    expect(confirmButton).toBeEnabled()
  })

  it('calls onConfirm when confirmed after review', () => {
    const onConfirm = vi.fn()

    render(
      <ReviewGuardModal
        open
        onClose={vi.fn()}
        onConfirm={onConfirm}
        action="copy"
        subject="transcript"
      />
    )

    fireEvent.click(screen.getByLabelText("I've reviewed the transcript"))
    fireEvent.click(screen.getByRole('button', { name: 'Confirm' }))

    expect(onConfirm).toHaveBeenCalledTimes(1)
  })

  it('calls onClose when cancelled', () => {
    const onClose = vi.fn()

    render(
      <ReviewGuardModal
        open
        onClose={onClose}
        onConfirm={vi.fn()}
        action="download"
        subject="document"
      />
    )

    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))

    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('calls onClose when Escape is pressed', () => {
    const onClose = vi.fn()

    render(
      <ReviewGuardModal
        open
        onClose={onClose}
        onConfirm={vi.fn()}
        action="copy"
        subject="document"
      />
    )

    fireEvent.keyDown(document, { key: 'Escape' })

    expect(onClose).toHaveBeenCalledTimes(1)
  })
})
