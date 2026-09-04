import { ReviewGuardButton } from '@/components/review-guard/review-guard-button'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

describe('<ReviewGuardButton />', () => {
  it('renders correct button text based on subject and action', () => {
    render(
      <ReviewGuardButton
        action="copy"
        subject="transcript"
        onConfirm={vi.fn()}
        onSuccess={vi.fn()}
      />
    )

    expect(
      screen.getByRole('button', { name: 'Copy transcript' })
    ).toBeInTheDocument()
  })

  it('opens the review modal when clicked', () => {
    render(
      <ReviewGuardButton
        action="download"
        subject="document"
        onConfirm={vi.fn()}
        onSuccess={vi.fn()}
      />
    )

    fireEvent.click(screen.getByRole('button', { name: 'Download document' }))

    expect(screen.getByText('Confirm review')).toBeInTheDocument()
  })

  it('does not open the modal when disabled', () => {
    render(
      <ReviewGuardButton
        action="copy"
        subject="document"
        disabled
        onConfirm={vi.fn()}
        onSuccess={vi.fn()}
      />
    )

    fireEvent.click(screen.getByRole('button', { name: 'Copy document' }))

    expect(screen.queryByText('Confirm review')).not.toBeInTheDocument()
  })

  it('calls onConfirm and onSuccess after review confirmation and closes the modal', async () => {
    const onConfirm = vi.fn().mockResolvedValue(true)
    const onSuccess = vi.fn()

    render(
      <ReviewGuardButton
        action="copy"
        subject="transcript"
        onConfirm={onConfirm}
        onSuccess={onSuccess}
      />
    )

    fireEvent.click(screen.getByRole('button', { name: 'Copy transcript' }))
    fireEvent.click(screen.getByLabelText("I've reviewed the transcript"))
    fireEvent.click(screen.getByRole('button', { name: 'Confirm' }))

    await waitFor(() => {
      expect(onConfirm).toHaveBeenCalledTimes(1)
    })

    await waitFor(() => {
      expect(onSuccess).toHaveBeenCalledTimes(1)
    })

    await waitFor(() => {
      expect(screen.queryByText('Confirm review')).not.toBeInTheDocument()
    })
  })

  it('closes the modal when cancelled', () => {
    render(
      <ReviewGuardButton
        action="download"
        subject="document"
        onConfirm={vi.fn()}
        onSuccess={vi.fn()}
      />
    )

    fireEvent.click(screen.getByRole('button', { name: 'Download document' }))
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))

    expect(screen.queryByText('Confirm review')).not.toBeInTheDocument()
  })
})
