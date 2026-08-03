import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import {
  TranscriptionTab,
  isEntryPlaying,
  buildTranscriptionHtml,
} from '@/app/transcriptions/[transcriptionId]/TranscriptionTab/TranscriptionTab'
import type { TranscriptionGetResponse } from '@/lib/client'
import { DialogueEntry } from '@/lib/client'

const updateDialogueEntryTextMock = vi.fn()
const updateDialogueEntrySpeakerMock = vi.fn()

vi.mock('@/hooks/use-update-transcription-speakers', () => ({
  useUpdateTranscription: () => ({
    updateDialogueEntryText: updateDialogueEntryTextMock,
    updateTitle: vi.fn(),
  }),
  useUpdateTranscriptionSpeakers: () => ({
    renameSpeakerEverywhere: vi.fn(),
    updateDialogueEntrySpeaker: updateDialogueEntrySpeakerMock,
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

vi.mock('@/components/download-button', () => ({
  DownloadButton: () => <div>Download</div>,
}))

vi.mock('@/components/ui/copy-button', () => ({
  default: () => <button type="button">Copy</button>,
}))

vi.mock('posthog-js', () => ({
  default: { capture: vi.fn() },
}))

describe('isEntryPlaying', () => {
  it('returns false when time is before entry start', () => {
    expect(isEntryPlaying(4, 5, 10)).toBe(false)
  })

  it('returns true when time equals entry start', () => {
    expect(isEntryPlaying(5, 5, 10)).toBe(true)
  })

  it('returns true when time is between entry and next entry', () => {
    expect(isEntryPlaying(7, 5, 10)).toBe(true)
  })

  it('returns false when time equals next entry start', () => {
    expect(isEntryPlaying(10, 5, 10)).toBe(false)
  })

  it('returns false when time is after next entry start', () => {
    expect(isEntryPlaying(12, 5, 10)).toBe(false)
  })

  it('handles last entry', () => {
    expect(isEntryPlaying(100, 5)).toBe(true)
  })

  it('handles last entry with time before start', () => {
    expect(isEntryPlaying(3, 5)).toBe(false)
  })
})

describe('buildTranscriptionHtml', () => {
  const mockTranscript: DialogueEntry[] = [
    { speaker: 'Alice', text: 'Hello', start_time: 0, end_time: 1 },
    { speaker: 'Bob', text: 'Hi', start_time: 1, end_time: 2 },
  ]

  it('formats a single entry', () => {
    const result = buildTranscriptionHtml(mockTranscript.slice(0, 1))

    expect(result).toBe('<p><b>Alice:</b> Hello</p>')
  })

  it('formats multiple entries with spacing', () => {
    const result = buildTranscriptionHtml(mockTranscript)

    expect(result).toBe('<p><b>Alice:</b> Hello</p>\n\n<p><b>Bob:</b> Hi</p>')
  })

  it('returns empty string for no entries', () => {
    expect(buildTranscriptionHtml([])).toBe('')
  })

  it('handles undefined input', () => {
    expect(buildTranscriptionHtml(undefined)).toBe('')
  })
})

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

describe('TranscriptionTab text edit rollback', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('rolls back the text to previous value when update request fails', async () => {
    updateDialogueEntryTextMock.mockRejectedValueOnce(new Error('Conflict'))

    render(<TranscriptionTab transcription={transcription} />)

    // Transcript is read-only until put into edit mode
    fireEvent.click(screen.getByRole('button', { name: 'Edit transcript' }))

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

describe('TranscriptionTab single speaker rename', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    updateDialogueEntrySpeakerMock.mockResolvedValue(undefined)
  })

  it('sends the original speaker name as expected_speaker, not the optimistically updated one', async () => {
    render(<TranscriptionTab transcription={transcription} />)

    // Speaker names are only editable in edit mode
    fireEvent.click(screen.getByRole('button', { name: 'Edit transcript' }))

    fireEvent.click(screen.getByText('Alice:'))

    const input = screen.getByRole('textbox')
    fireEvent.change(input, { target: { value: 'Bob' } })

    fireEvent.click(screen.getByText('Update this occurrence'))

    await waitFor(() => {
      expect(updateDialogueEntrySpeakerMock).toHaveBeenCalledWith(0, {
        new_speaker: 'Bob',
        expected_speaker: 'Alice',
        expected_start_time: 0,
        expected_end_time: 1,
      })
    })
  })
})
