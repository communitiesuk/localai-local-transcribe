import { render, screen, fireEvent } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { useState } from 'react'
import { TranscriptReviewModal } from '@/components/ui/transcript-review-modal'

const defaultProps = {
  open: true,
  onClose: vi.fn(),
  onConfirm: vi.fn(),
  titleId: 'test-modal-title',
}

describe('<TranscriptReviewModal />', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('visibility', () => {
    it('renders nothing when open is false', () => {
      render(<TranscriptReviewModal {...defaultProps} open={false} />)
      expect(screen.queryByText('Confirm review')).not.toBeInTheDocument()
    })

    it('renders the modal when open is true', () => {
      render(<TranscriptReviewModal {...defaultProps} />)
      expect(screen.getByText('Confirm review')).toBeInTheDocument()
    })
  })

  describe('content', () => {
    it('shows the AI accuracy warning', () => {
      render(<TranscriptReviewModal {...defaultProps} />)
      expect(
        screen.getByText(/AI transcription is not 100% accurate/i)
      ).toBeInTheDocument()
    })

    it('shows the review requirement message', () => {
      render(<TranscriptReviewModal {...defaultProps} />)
      expect(
        screen.getByText(/you must confirm that you've reviewed the transcript/i)
      ).toBeInTheDocument()
    })

    it('renders the review checkbox', () => {
      render(<TranscriptReviewModal {...defaultProps} />)
      expect(
        screen.getByRole('checkbox', { name: /i've reviewed the transcript/i })
      ).toBeInTheDocument()
    })
  })

  describe('checkbox gates the Confirm button', () => {
    it('Confirm button is disabled when checkbox is unchecked', () => {
      render(<TranscriptReviewModal {...defaultProps} />)
      expect(screen.getByRole('button', { name: 'Confirm' })).toBeDisabled()
    })

    it('Confirm button is enabled after the checkbox is checked', () => {
      render(<TranscriptReviewModal {...defaultProps} />)
      fireEvent.click(
        screen.getByRole('checkbox', { name: /i've reviewed the transcript/i })
      )
      expect(screen.getByRole('button', { name: 'Confirm' })).toBeEnabled()
    })
  })

  describe('confirm action', () => {
    it('calls onConfirm when Confirm is clicked with checkbox checked', () => {
      const onConfirm = vi.fn()
      render(<TranscriptReviewModal {...defaultProps} onConfirm={onConfirm} />)
      fireEvent.click(
        screen.getByRole('checkbox', { name: /i've reviewed the transcript/i })
      )
      fireEvent.click(screen.getByRole('button', { name: 'Confirm' }))
      expect(onConfirm).toHaveBeenCalledOnce()
    })

    it('does not call onConfirm when Confirm is clicked without checking the checkbox', () => {
      const onConfirm = vi.fn()
      render(<TranscriptReviewModal {...defaultProps} onConfirm={onConfirm} />)
      fireEvent.click(screen.getByRole('button', { name: 'Confirm' }))
      expect(onConfirm).not.toHaveBeenCalled()
    })
  })

  describe('cancel action', () => {
    it('calls onClose when Cancel is clicked', () => {
      const onClose = vi.fn()
      render(<TranscriptReviewModal {...defaultProps} onClose={onClose} />)
      fireEvent.click(screen.getByRole('link', { name: 'Cancel' }))
      expect(onClose).toHaveBeenCalledOnce()
    })

    it('calls onClose when the close button is clicked', () => {
      const onClose = vi.fn()
      render(<TranscriptReviewModal {...defaultProps} onClose={onClose} />)
      fireEvent.click(screen.getByRole('button', { name: 'Close' }))
      expect(onClose).toHaveBeenCalledOnce()
    })
  })

  describe('checkbox resets on close', () => {
    it('unchecks the checkbox when the modal is closed via Cancel and reopened', () => {
      function Wrapper() {
        const [open, setOpen] = useState(true)
        return (
          <>
            <button onClick={() => setOpen(true)}>Reopen</button>
            <TranscriptReviewModal
              open={open}
              onClose={() => setOpen(false)}
              onConfirm={vi.fn()}
              titleId="test-modal"
            />
          </>
        )
      }

      render(<Wrapper />)

      fireEvent.click(
        screen.getByRole('checkbox', { name: /i've reviewed the transcript/i })
      )
      expect(
        screen.getByRole('checkbox', { name: /i've reviewed the transcript/i })
      ).toBeChecked()

      fireEvent.click(screen.getByRole('link', { name: 'Cancel' }))

      fireEvent.click(screen.getByRole('button', { name: 'Reopen' }))

      expect(
        screen.getByRole('checkbox', { name: /i've reviewed the transcript/i })
      ).not.toBeChecked()
    })
  })
})
