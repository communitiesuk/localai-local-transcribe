import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { CopyTranscriptButton } from '@/components/ui/copy-transcript-button'

const clipboardWriteMock = vi.fn()
const clipboardWriteTextMock = vi.fn()

const posthogCaptureMock = vi.hoisted(() => vi.fn())
vi.mock('posthog-js', () => ({
  default: { capture: posthogCaptureMock },
}))

// ClipboardItem is not available in jsdom — the component falls back to writeText
global.ClipboardItem = undefined as unknown as typeof ClipboardItem

beforeEach(() => {
  vi.clearAllMocks()
  Object.assign(navigator, {
    clipboard: {
      write: clipboardWriteMock,
      writeText: clipboardWriteTextMock.mockResolvedValue(undefined),
    },
  })
})

const openModal = () => {
  fireEvent.click(screen.getByRole('button', { name: 'Copy transcript' }))
}

const checkReviewCheckbox = () => {
  fireEvent.click(
    screen.getByRole('checkbox', { name: /i've reviewed the transcript/i })
  )
}

describe('<CopyTranscriptButton />', () => {
  const textToCopy = '<p><b>Alice:</b> Hello</p>'
  const onSuccess = vi.fn()

  describe('trigger button', () => {
    it('renders the Copy transcript button', () => {
      render(<CopyTranscriptButton textToCopy={textToCopy} onSuccess={onSuccess} />)
      expect(
        screen.getByRole('button', { name: 'Copy transcript' })
      ).toBeInTheDocument()
    })

    it('opens the review modal when clicked', () => {
      render(<CopyTranscriptButton textToCopy={textToCopy} onSuccess={onSuccess} />)
      openModal()
      expect(screen.getByText('Confirm review')).toBeInTheDocument()
    })
  })

  describe('confirm flow', () => {
    it('copies to clipboard and calls onSuccess after confirming with checkbox checked', async () => {
      render(<CopyTranscriptButton textToCopy={textToCopy} onSuccess={onSuccess} />)
      openModal()
      checkReviewCheckbox()
      fireEvent.click(screen.getByRole('button', { name: 'Confirm' }))

      await waitFor(() => {
        expect(clipboardWriteTextMock).toHaveBeenCalledWith('Alice: Hello')
        expect(onSuccess).toHaveBeenCalledOnce()
      })
    })

    it('closes the modal after a successful confirm', async () => {
      render(<CopyTranscriptButton textToCopy={textToCopy} onSuccess={onSuccess} />)
      openModal()
      checkReviewCheckbox()
      fireEvent.click(screen.getByRole('button', { name: 'Confirm' }))

      await waitFor(() => {
        expect(screen.queryByText('Confirm review')).not.toBeInTheDocument()
      })
    })
  })

  describe('cancel / dismiss flow', () => {
    it('does not copy or call onSuccess when Cancel is clicked', () => {
      render(<CopyTranscriptButton textToCopy={textToCopy} onSuccess={onSuccess} />)
      openModal()
      fireEvent.click(screen.getByRole('link', { name: 'Cancel' }))

      expect(clipboardWriteMock).not.toHaveBeenCalled()
      expect(clipboardWriteTextMock).not.toHaveBeenCalled()
      expect(onSuccess).not.toHaveBeenCalled()
    })

    it('does not copy or call onSuccess when the close button is clicked', () => {
      render(<CopyTranscriptButton textToCopy={textToCopy} onSuccess={onSuccess} />)
      openModal()
      fireEvent.click(screen.getByRole('button', { name: 'Close' }))

      expect(clipboardWriteMock).not.toHaveBeenCalled()
      expect(clipboardWriteTextMock).not.toHaveBeenCalled()
      expect(onSuccess).not.toHaveBeenCalled()
    })

    it('dismisses the modal when Cancel is clicked', () => {
      render(<CopyTranscriptButton textToCopy={textToCopy} onSuccess={onSuccess} />)
      openModal()
      fireEvent.click(screen.getByRole('link', { name: 'Cancel' }))
      expect(screen.queryByText('Confirm review')).not.toBeInTheDocument()
    })
  })
})
