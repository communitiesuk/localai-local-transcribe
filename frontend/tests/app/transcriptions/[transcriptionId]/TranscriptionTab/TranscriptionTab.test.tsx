import {
  render,
  screen,
  fireEvent,
  waitFor,
  within,
} from '@testing-library/react'
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
const renameSpeakerEverywhereMock = vi.fn()
const setBannerMock = vi.fn()
const clearBannerMock = vi.fn()
const onLineEditErrorMock = vi.fn()

vi.mock('@/hooks/use-update-transcription-speakers', () => ({
  useUpdateTranscription: () => ({
    updateDialogueEntryText: updateDialogueEntryTextMock,
    updateTitle: vi.fn(),
  }),
  useUpdateTranscriptionSpeakers: () => ({
    renameSpeakerEverywhere: renameSpeakerEverywhereMock,
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
    SpeakerEditor: ({ disabled }: { disabled?: boolean }) => (
      <button type="button" disabled={disabled}>
        Edit speaker names
      </button>
    ),
  })
)

vi.mock('@/components/ui/copy-button', () => ({
  default: ({ disabled }: { disabled?: boolean }) => (
    <button type="button" disabled={disabled}>
      Copy
    </button>
  ),
}))

vi.mock('@/stores/use-banner-store', () => ({
  useBannerStore: () => ({
    setBanner: setBannerMock,
    clearBanner: clearBannerMock,
  }),
}))

vi.mock('posthog-js', () => ({
  default: { capture: vi.fn() },
}))

const renderTab = (transcription: TranscriptionGetResponse) =>
  render(
    <TranscriptionTab
      transcription={transcription}
      onLineEditError={onLineEditErrorMock}
    />
  )

const renderTabWithDismissBanner = (
  transcription: TranscriptionGetResponse,
  onDismissBanner: () => void
) =>
  render(
    <TranscriptionTab
      transcription={transcription}
      onLineEditError={onLineEditErrorMock}
      onDismissBanner={onDismissBanner}
    />
  )

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
    expect(buildTranscriptionHtml(mockTranscript.slice(0, 1))).toBe(
      '<p><b>Alice:</b> Hello</p>'
    )
  })

  it('formats multiple entries with spacing', () => {
    expect(buildTranscriptionHtml(mockTranscript)).toBe(
      '<p><b>Alice:</b> Hello</p>\n\n<p><b>Bob:</b> Hi</p>'
    )
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
    { speaker: 'Alice', text: 'Original text', start_time: 0, end_time: 1 },
  ],
  status: 'completed',
  created_datetime: '2024-01-01T00:00:00Z',
  case_id: 'case-1',
  client_name: 'Test Client',
  client_date_of_birth: '1990-01-01',
}

const twoEntryTranscription: TranscriptionGetResponse = {
  ...transcription,
  dialogue_entries: [
    { speaker: 'Alice', text: 'First line', start_time: 0, end_time: 1 },
    { speaker: 'Bob', text: 'Second line', start_time: 1, end_time: 2 },
  ],
}

describe('TranscriptionTab default view', () => {
  beforeEach(() => vi.clearAllMocks())

  it('renders the four action buttons', () => {
    renderTab(transcription)
    expect(
      screen.getByRole('button', { name: 'Edit speaker names' })
    ).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: 'Edit transcript' })
    ).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: 'Copy transcript' })
    ).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: 'Download transcript' })
    ).toBeInTheDocument()
  })

  it('does not show line edit buttons in default view', () => {
    renderTab(transcription)
    expect(
      screen.queryByRole('button', { name: 'Save line edit' })
    ).not.toBeInTheDocument()
    expect(
      screen.queryByRole('button', { name: 'Cancel line edit' })
    ).not.toBeInTheDocument()
    expect(
      screen.queryByRole('button', { name: 'Finish editing' })
    ).not.toBeInTheDocument()
  })

  it('does not show radio buttons in default view', () => {
    renderTab(transcription)
    expect(screen.queryByRole('radio')).not.toBeInTheDocument()
  })
})

describe('TranscriptionTab entering line edit mode', () => {
  beforeEach(() => vi.clearAllMocks())

  it('disables the four action buttons when edit mode is active', () => {
    renderTab(transcription)
    fireEvent.click(screen.getByRole('button', { name: 'Edit transcript' }))

    expect(
      screen.getByRole('button', { name: 'Edit speaker names' })
    ).toBeDisabled()
    expect(
      screen.getByRole('button', { name: 'Edit transcript' })
    ).toBeDisabled()
    expect(
      screen.getByRole('button', { name: 'Copy transcript' })
    ).toBeDisabled()
    expect(
      screen.getByRole('button', { name: 'Download transcript' })
    ).toBeDisabled()
  })

  it('shows Save line edit, Cancel line edit and Finish editing buttons', () => {
    renderTab(transcription)
    fireEvent.click(screen.getByRole('button', { name: 'Edit transcript' }))

    expect(
      screen.getByRole('button', { name: 'Save line edit' })
    ).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: 'Cancel line edit' })
    ).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: 'Finish editing' })
    ).toBeInTheDocument()
  })

  it('shows a radio button per dialogue entry', () => {
    renderTab(twoEntryTranscription)
    fireEvent.click(screen.getByRole('button', { name: 'Edit transcript' }))

    expect(screen.getAllByRole('radio')).toHaveLength(2)
  })

  it('Save line edit and Cancel line edit are disabled until text is entered in the textarea', () => {
    renderTab(transcription)
    fireEvent.click(screen.getByRole('button', { name: 'Edit transcript' }))

    expect(
      screen.getByRole('button', { name: 'Save line edit' })
    ).toBeDisabled()
    expect(
      screen.getByRole('button', { name: 'Cancel line edit' })
    ).toBeDisabled()
  })

  it('enables Save line edit and Cancel line edit after text is entered in the textarea', () => {
    renderTab(transcription)
    fireEvent.click(screen.getByRole('button', { name: 'Edit transcript' }))
    fireEvent.input(screen.getByText('Original text'))

    expect(
      screen.getByRole('button', { name: 'Save line edit' })
    ).not.toBeDisabled()
    expect(
      screen.getByRole('button', { name: 'Cancel line edit' })
    ).not.toBeDisabled()
  })
})

describe('TranscriptionTab finish editing validation', () => {
  beforeEach(() => vi.clearAllMocks())

  it('calls onLineEditError when Finish editing is clicked while an edit is in progress', () => {
    renderTab(transcription)
    fireEvent.click(screen.getByRole('button', { name: 'Edit transcript' }))
    fireEvent.input(screen.getByText('Original text'))
    fireEvent.click(screen.getByRole('button', { name: 'Finish editing' }))

    expect(onLineEditErrorMock).toHaveBeenCalledWith(
      'You must save or cancel your line edit to finish editing'
    )
  })

  it('calls onLineEditError when switching to another radio while an edit is in progress', () => {
    renderTab(twoEntryTranscription)
    fireEvent.click(screen.getByRole('button', { name: 'Edit transcript' }))
    fireEvent.input(screen.getByText('First line'))
    fireEvent.click(
      screen.getByRole('radio', { name: 'Select line 2 to edit' })
    )

    expect(onLineEditErrorMock).toHaveBeenCalledWith(
      'You must save or cancel your line edit to finish editing'
    )
  })

  it('clears the error when Finish editing is clicked after cancel', () => {
    renderTab(transcription)
    fireEvent.click(screen.getByRole('button', { name: 'Edit transcript' }))
    fireEvent.click(
      screen.getByRole('radio', { name: 'Select line 1 to edit' })
    )
    fireEvent.click(screen.getByRole('button', { name: 'Cancel line edit' }))
    fireEvent.click(screen.getByRole('button', { name: 'Finish editing' }))

    expect(onLineEditErrorMock).toHaveBeenLastCalledWith(null)
  })
})

describe('TranscriptionTab finishing editing', () => {
  beforeEach(() => vi.clearAllMocks())

  it('returns to default view after Finish editing with no active edit', () => {
    renderTab(transcription)
    fireEvent.click(screen.getByRole('button', { name: 'Edit transcript' }))
    fireEvent.click(screen.getByRole('button', { name: 'Finish editing' }))

    expect(
      screen.queryByRole('button', { name: 'Save line edit' })
    ).not.toBeInTheDocument()
    expect(
      screen.queryByRole('button', { name: 'Cancel line edit' })
    ).not.toBeInTheDocument()
    expect(
      screen.queryByRole('button', { name: 'Finish editing' })
    ).not.toBeInTheDocument()

    expect(
      screen.getByRole('button', { name: 'Edit transcript' })
    ).not.toBeDisabled()
    expect(screen.queryByRole('radio')).not.toBeInTheDocument()
  })
})

describe('TranscriptionTab cancel line edit', () => {
  beforeEach(() => vi.clearAllMocks())

  it('reverts the edited text on cancel', () => {
    renderTab(transcription)
    fireEvent.click(screen.getByRole('button', { name: 'Edit transcript' }))

    const text = screen.getByText('Original text')
    fireEvent.click(text)
    fireEvent.input(text)
    Object.defineProperty(text, 'innerText', {
      value: 'Changed text',
      configurable: true,
    })
    fireEvent.blur(text)

    fireEvent.click(screen.getByRole('button', { name: 'Cancel line edit' }))

    expect(screen.getByText('Original text')).toBeInTheDocument()
  })

  it('disables Save and Cancel after cancelling', () => {
    renderTab(transcription)
    fireEvent.click(screen.getByRole('button', { name: 'Edit transcript' }))
    fireEvent.input(screen.getByText('Original text'))
    fireEvent.click(screen.getByRole('button', { name: 'Cancel line edit' }))

    expect(
      screen.getByRole('button', { name: 'Save line edit' })
    ).toBeDisabled()
    expect(
      screen.getByRole('button', { name: 'Cancel line edit' })
    ).toBeDisabled()
  })
})

describe('TranscriptionTab save line edit', () => {
  beforeEach(() => vi.clearAllMocks())

  it('shows the success banner after a successful save', async () => {
    updateDialogueEntryTextMock.mockResolvedValue(undefined)
    renderTab(transcription)

    fireEvent.click(screen.getByRole('button', { name: 'Edit transcript' }))
    fireEvent.input(screen.getByText('Original text'))
    fireEvent.click(screen.getByRole('button', { name: 'Save line edit' }))

    await waitFor(() => {
      expect(setBannerMock).toHaveBeenCalledWith({
        variant: 'success',
        title: 'Success',
        message: 'Line edit saved',
      })
    })
  })

  it('rolls back the text when the save API call fails', async () => {
    updateDialogueEntryTextMock.mockRejectedValueOnce(new Error('Conflict'))
    renderTab(transcription)

    fireEvent.click(screen.getByRole('button', { name: 'Edit transcript' }))

    const text = screen.getByText('Original text')
    fireEvent.click(text)
    fireEvent.input(text)
    Object.defineProperty(text, 'innerText', {
      value: 'Edited text',
      configurable: true,
    })
    fireEvent.blur(text)

    fireEvent.click(screen.getByRole('button', { name: 'Save line edit' }))

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
    renderTab(transcription)

    fireEvent.click(
      screen.getByRole('button', { name: 'Edit speaker name Alice' })
    )

    const input = screen.getByRole('textbox')
    fireEvent.change(input, { target: { value: 'Bob' } })
    fireEvent.click(
      screen.getByRole('button', { name: 'Update this occurrence' })
    )

    await waitFor(() => {
      expect(updateDialogueEntrySpeakerMock).toHaveBeenCalledWith(0, {
        new_speaker: 'Bob',
        expected_speaker: 'Alice',
        expected_start_time: 0,
        expected_end_time: 1,
      })
    })
  })

  it('clears existing banners when opening the speaker edit modal', () => {
    const onDismissBanner = vi.fn()
    renderTabWithDismissBanner(transcription, onDismissBanner)

    fireEvent.click(
      screen.getByRole('button', { name: 'Edit speaker name Alice' })
    )

    expect(
      screen.getByRole('heading', { name: "Edit 'Alice'" })
    ).toBeInTheDocument()
    expect(onDismissBanner).toHaveBeenCalledOnce()
  })

  it('closes the speaker edit modal when cancelling with no changes', () => {
    renderTab(transcription)

    fireEvent.click(
      screen.getByRole('button', { name: 'Edit speaker name Alice' })
    )
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('shows an error in the speaker edit modal and keeps it open when updating one occurrence fails', async () => {
    updateDialogueEntrySpeakerMock.mockRejectedValueOnce(new Error('Conflict'))
    renderTab(transcription)

    fireEvent.click(
      screen.getByRole('button', { name: 'Edit speaker name Alice' })
    )
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'Bob' } })
    fireEvent.click(
      screen.getByRole('button', { name: 'Update this occurrence' })
    )

    const dialog = screen.getByRole('dialog')
    expect(
      await within(dialog).findByText(
        'One or more speaker names could not be updated, please try again.'
      )
    ).toBeInTheDocument()
    expect(setBannerMock).not.toHaveBeenCalled()
    expect(dialog).toBeInTheDocument()
    expect(screen.getByRole('textbox')).toHaveValue('Bob')
  })

  it('shows an error in the speaker edit modal and keeps it open when updating all occurrences fails', async () => {
    renameSpeakerEverywhereMock.mockRejectedValueOnce(new Error('Conflict'))
    renderTab(transcription)

    fireEvent.click(
      screen.getByRole('button', { name: 'Edit speaker name Alice' })
    )
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'Bob' } })
    fireEvent.click(
      screen.getByRole('button', { name: 'Update all occurrences' })
    )

    const dialog = screen.getByRole('dialog')
    expect(
      await within(dialog).findByText(
        'One or more speaker names could not be updated, please try again.'
      )
    ).toBeInTheDocument()
    expect(setBannerMock).not.toHaveBeenCalled()
    expect(dialog).toBeInTheDocument()
    expect(screen.getByRole('textbox')).toHaveValue('Bob')
  })

  it('clears the speaker edit modal error when cancelling after a failed update', async () => {
    renameSpeakerEverywhereMock.mockRejectedValueOnce(new Error('Conflict'))
    renderTab(transcription)

    fireEvent.click(
      screen.getByRole('button', { name: 'Edit speaker name Alice' })
    )
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'Bob' } })
    fireEvent.click(
      screen.getByRole('button', { name: 'Update all occurrences' })
    )

    expect(
      await screen.findByText(
        'One or more speaker names could not be updated, please try again.'
      )
    ).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))

    expect(
      screen.queryByText(
        'One or more speaker names could not be updated, please try again.'
      )
    ).not.toBeInTheDocument()
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })
})

describe('TranscriptionTab full edit flow', () => {
  beforeEach(() => vi.clearAllMocks())

  it('disables action buttons on entering edit mode, shows banner on save, and clears it on finish editing', async () => {
    updateDialogueEntryTextMock.mockResolvedValue(undefined)
    renderTab(transcription)

    fireEvent.click(screen.getByRole('button', { name: 'Edit transcript' }))

    expect(
      screen.getByRole('button', { name: 'Edit speaker names' })
    ).toBeDisabled()
    expect(
      screen.getByRole('button', { name: 'Edit transcript' })
    ).toBeDisabled()
    expect(
      screen.getByRole('button', { name: 'Copy transcript' })
    ).toBeDisabled()
    expect(
      screen.getByRole('button', { name: 'Download transcript' })
    ).toBeDisabled()
    expect(
      screen.getByRole('button', { name: 'Save line edit' })
    ).toBeDisabled()
    expect(
      screen.getByRole('button', { name: 'Cancel line edit' })
    ).toBeDisabled()
    expect(
      screen.getByRole('button', { name: 'Finish editing' })
    ).not.toBeDisabled()

    fireEvent.input(screen.getByText('Original text'))
    fireEvent.click(screen.getByRole('button', { name: 'Save line edit' }))

    await waitFor(() => {
      expect(setBannerMock).toHaveBeenCalledWith({
        variant: 'success',
        title: 'Success',
        message: 'Line edit saved',
      })
    })

    fireEvent.click(screen.getByRole('button', { name: 'Finish editing' }))
    expect(clearBannerMock).toHaveBeenCalled()
  })
})
