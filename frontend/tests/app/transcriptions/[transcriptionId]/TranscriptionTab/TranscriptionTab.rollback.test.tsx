import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { TranscriptionTab } from '@/app/transcriptions/[transcriptionId]/TranscriptionTab/TranscriptionTab'
import type { TranscriptionGetResponse } from '@/lib/client'

const updateDialogueEntryTextMock = vi.fn()

vi.mock('@/hooks/use-update-transcription-speakers', () => ({
  useUpdateTranscription: () => ({
    updateDialogueEntryText: updateDialogueEntryTextMock,
    updateTitle: vi.fn(),
  }),
  useUpdateTranscriptionSpeakers: () => ({
    renameSpeakerEverywhere: vi.fn(),
    updateDialogueEntrySpeaker: vi.fn(),
  }),
}))

vi.mock('@tanstack/react-query', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@tanstack/react-query')>()
  return {
    ...actual,
    useQuery: vi.fn(() => ({ data: undefined })),
  }
})

vi.mock(
  '@/app/transcriptions/[transcriptionId]/TranscriptionTab/SpeakerEditor',
  () => ({
    SpeakerEditor: () => <div>Speaker editor</div>,
  })
)

vi.mock(
  '@/app/transcriptions/[transcriptionId]/TranscriptionTab/SpeakerNamePopover',
  () => ({
    SpeakerNamePopover: () => <div>Speaker popover</div>,
  })
)

vi.mock('@/components/download-button', () => ({
  DownloadButton: () => <div>Download</div>,
}))

vi.mock('@/components/ui/copy-button', () => ({
  default: () => <button type="button">Copy</button>,
}))

describe('TranscriptionTab text edit rollback', () => {
  const transcription: TranscriptionGetResponse = {
    id: 'transcription-1',
    title: 'Test title',
    dialogue_entries: [
      {
        speaker: 'Alice',
        text: 'Original text',
        start_time: 0,
        end_time: 1,
      },
    ],
    status: 'completed',
    created_datetime: '2024-01-01T00:00:00Z',
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('rolls back the text to previous value when update request fails', async () => {
    updateDialogueEntryTextMock.mockRejectedValueOnce(new Error('Conflict'))

    render(<TranscriptionTab transcription={transcription} />)

    const text = screen.getByText('Original text')

    fireEvent.click(text)
    text.innerText = 'Edited text'
    fireEvent.blur(text)

    await waitFor(() => {
      expect(updateDialogueEntryTextMock).toHaveBeenCalledWith(0, {
        new_text: 'Edited text',
        expected_text: 'Original text',
        expected_speaker: 'Alice',
        expected_start_time: 0,
        expected_end_time: 1,
      })
    })

    await waitFor(() => {
      expect(screen.getByText('Original text')).toBeInTheDocument()
    })
  })
})
