import { describe, it, vi, expect, beforeAll } from 'vitest'
import { render, screen } from '@testing-library/react'
import SimpleEditor from '@/app/transcriptions/[transcriptionId]/MinuteTab/components/editor/tiptap-editor'
import { TranscriptionGetResponse } from '@/lib/client'
import userEvent from '@testing-library/user-event'

const transcriptionWithEntries: TranscriptionGetResponse = {
  id: 'transcription-1',
  title: null,
  dialogue_entries: [
    { speaker: 'Speaker 0', text: 'Entry 0', start_time: 0, end_time: 1 },
    { speaker: 'Speaker 1', text: 'Entry 1', start_time: 1, end_time: 2 },
  ],
  status: 'completed',
  created_datetime: '2024-01-01T00:00:00Z',
  client_name: null,
  case_id: null,
  client_date_of_birth: null,
}

describe('<SimpleEditor />', () => {
  beforeAll(() => {
    // We stub this method because tiptap expects to be running in a real DOM
    // and so this method to be present. The tests, however, run with jsDOM
    // where this function doesn't exist.
    document.elementFromPoint = () => null
  })

  it('Should call focusDialogEntry on quote click with quote index', async () => {
    const onCitationClicked = vi.fn()

    render(
      <SimpleEditor
        initialContent={'test content[1]'}
        onContentChange={() => null}
        isEditing={false}
        currentTranscription={transcriptionWithEntries}
        hideCitations={false}
        onCitationClicked={onCitationClicked}
      />
    )

    const citationLink = screen.getByText('[1]')
    expect(citationLink).toBeInTheDocument()

    await userEvent.click(citationLink)
    expect(onCitationClicked).toHaveBeenCalledWith(1)
  })
})
