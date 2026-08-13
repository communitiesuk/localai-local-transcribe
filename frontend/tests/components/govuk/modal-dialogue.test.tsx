import { render, screen, fireEvent } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { GovukModalDialogue } from '@/components/govuk/modal-dialogue'

const defaultProps = {
  open: true,
  onClose: vi.fn(),
  title: 'Test modal title',
  titleId: 'test-modal-title',
}

describe('<GovukModalDialogue />', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('visibility', () => {
    it('renders nothing when open is false', () => {
      render(<GovukModalDialogue {...defaultProps} open={false} />)
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    })

    it('renders the dialog when open is true', () => {
      render(<GovukModalDialogue {...defaultProps} />)
      expect(screen.getByRole('dialog')).toBeInTheDocument()
    })
  })

  describe('content', () => {
    it('renders the title', () => {
      render(<GovukModalDialogue {...defaultProps} />)
      expect(screen.getByText('Test modal title')).toBeInTheDocument()
    })

    it('renders children inside the dialog', () => {
      render(
        <GovukModalDialogue {...defaultProps}>
          <p>Modal body content</p>
        </GovukModalDialogue>
      )
      expect(screen.getByText('Modal body content')).toBeInTheDocument()
    })
  })

  describe('accessibility', () => {
    it('sets aria-modal on the dialog element', () => {
      render(<GovukModalDialogue {...defaultProps} />)
      expect(screen.getByRole('dialog')).toHaveAttribute('aria-modal', 'true')
    })

    it('labels the dialog with the titleId', () => {
      render(<GovukModalDialogue {...defaultProps} />)
      expect(screen.getByRole('dialog')).toHaveAttribute(
        'aria-labelledby',
        'test-modal-title'
      )
    })

    it('labels the dialog description with the descriptionId', () => {
      render(
        <GovukModalDialogue
          {...defaultProps}
          descriptionId="test-modal-desc"
        />
      )
      expect(screen.getByRole('dialog')).toHaveAttribute(
        'aria-describedby',
        'test-modal-desc'
      )
    })

    it('sets inert on .govuk-modal-dialogue-inert-container when open and removes it when closed', () => {
      const container = document.createElement('div')
      container.className = 'govuk-modal-dialogue-inert-container'
      document.body.appendChild(container)

      const { rerender } = render(<GovukModalDialogue {...defaultProps} />)
      expect(container.hasAttribute('inert')).toBe(true)

      rerender(<GovukModalDialogue {...defaultProps} open={false} />)
      expect(container.hasAttribute('inert')).toBe(false)

      document.body.removeChild(container)
    })
  })

  describe('close behaviour', () => {
    it('calls onClose when the close button is clicked', () => {
      const onClose = vi.fn()
      render(<GovukModalDialogue {...defaultProps} onClose={onClose} />)
      fireEvent.click(screen.getByRole('button', { name: 'Close' }))
      expect(onClose).toHaveBeenCalledOnce()
    })

    it('calls onClose when the Escape key is pressed', () => {
      const onClose = vi.fn()
      render(<GovukModalDialogue {...defaultProps} onClose={onClose} />)
      fireEvent.keyDown(document, { key: 'Escape' })
      expect(onClose).toHaveBeenCalledOnce()
    })

    it('does not call onClose when Escape is pressed and modal is closed', () => {
      const onClose = vi.fn()
      render(<GovukModalDialogue {...defaultProps} open={false} onClose={onClose} />)
      fireEvent.keyDown(document, { key: 'Escape' })
      expect(onClose).not.toHaveBeenCalled()
    })

    it('calls onClose when clicking the wrapper outside the dialog box', () => {
      const onClose = vi.fn()
      render(<GovukModalDialogue {...defaultProps} onClose={onClose} />)
      const wrapper = document.querySelector('.govuk-modal-dialogue__wrapper')!
      fireEvent.click(wrapper)
      expect(onClose).toHaveBeenCalledOnce()
    })

    it('does not call onClose when clicking inside the dialog box', () => {
      const onClose = vi.fn()
      render(
        <GovukModalDialogue {...defaultProps} onClose={onClose}>
          <p>Inner content</p>
        </GovukModalDialogue>
      )
      fireEvent.click(screen.getByText('Inner content'))
      expect(onClose).not.toHaveBeenCalled()
    })
  })
})
