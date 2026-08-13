import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { DownloadTranscriptButton } from '@/components/recordings/download-transcript-button'
import type { DialogueEntry } from '@/lib/client'

const downloadTranscriptDocMock = vi.hoisted(() => vi.fn())
vi.mock('@/lib/download-word-doc', () => ({
  downloadTranscriptDoc: downloadTranscriptDocMock,
}))

const entries: DialogueEntry[] = [
  { speaker: 'Alice', text: 'Hello', start_time: 0, end_time: 1 },
  { speaker: 'Bob', text: 'Hi', start_time: 1, end_time: 2 },
]

const openModal = () =>
  fireEvent.click(screen.getByRole('button', { name: 'Download transcript' }))

const checkReviewCheckbox = () =>
  fireEvent.click(
    screen.getByRole('checkbox', { name: /i've reviewed the transcript/i })
  )

describe('<DownloadTranscriptButton />', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    downloadTranscriptDocMock.mockResolvedValue(undefined)
  })

  describe('trigger button', () => {
    it('renders the Download transcript button', () => {
      render(<DownloadTranscriptButton getEntries={() => entries} />)
      expect(
        screen.getByRole('button', { name: 'Download transcript' })
      ).toBeInTheDocument()
    })

    it('opens the review modal when clicked', () => {
      render(<DownloadTranscriptButton getEntries={() => entries} />)
      openModal()
      expect(screen.getByText('Confirm review')).toBeInTheDocument()
    })
  })

  describe('confirm flow', () => {
    it('calls downloadTranscriptDoc with the entries returned by getEntries on confirm', async () => {
      render(<DownloadTranscriptButton getEntries={() => entries} />)
      openModal()
      checkReviewCheckbox()
      fireEvent.click(screen.getByRole('button', { name: 'Confirm' }))

      await waitFor(() => {
        expect(downloadTranscriptDocMock).toHaveBeenCalledWith(entries)
      })
    })

    it('uses the latest entries from getEntries at the time of confirm', async () => {
      let currentEntries = entries
      render(<DownloadTranscriptButton getEntries={() => currentEntries} />)

      openModal()
      // Simulate entries changing after modal opens
      const updatedEntries: DialogueEntry[] = [
        { speaker: 'Charlie', text: 'Updated', start_time: 0, end_time: 1 },
      ]
      currentEntries = updatedEntries

      checkReviewCheckbox()
      fireEvent.click(screen.getByRole('button', { name: 'Confirm' }))

      await waitFor(() => {
        expect(downloadTranscriptDocMock).toHaveBeenCalledWith(updatedEntries)
      })
    })

    it('closes the modal after a successful confirm', async () => {
      render(<DownloadTranscriptButton getEntries={() => entries} />)
      openModal()
      checkReviewCheckbox()
      fireEvent.click(screen.getByRole('button', { name: 'Confirm' }))

      await waitFor(() => {
        expect(screen.queryByText('Confirm review')).not.toBeInTheDocument()
      })
    })
  })

  describe('cancel / dismiss flow', () => {
    it('does not call downloadTranscriptDoc when Cancel is clicked', () => {
      render(<DownloadTranscriptButton getEntries={() => entries} />)
      openModal()
      fireEvent.click(screen.getByRole('link', { name: 'Cancel' }))
      expect(downloadTranscriptDocMock).not.toHaveBeenCalled()
    })

    it('does not call downloadTranscriptDoc when the close button is clicked', () => {
      render(<DownloadTranscriptButton getEntries={() => entries} />)
      openModal()
      fireEvent.click(screen.getByRole('button', { name: 'Close' }))
      expect(downloadTranscriptDocMock).not.toHaveBeenCalled()
    })

    it('dismisses the modal when Cancel is clicked', () => {
      render(<DownloadTranscriptButton getEntries={() => entries} />)
      openModal()
      fireEvent.click(screen.getByRole('link', { name: 'Cancel' }))
      expect(screen.queryByText('Confirm review')).not.toBeInTheDocument()
    })
  })
})
