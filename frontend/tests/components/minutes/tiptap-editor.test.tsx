import { describe, it, vi, expect, beforeAll } from 'vitest'
import { render, screen } from '@testing-library/react'
import SimpleEditor from '@/app/transcriptions/[transcriptionId]/MinuteTab/components/editor/tiptap-editor'
import { TranscriptionGetResponse } from '@/lib/client'
import userEvent from '@testing-library/user-event'

describe('<SimpleEditor />', () => {
  beforeAll(() => {
    // We stub this method because tiptap expects to be running in a real DOM
    // and so this method to be present. The tests, however, run with jsDOM
    // where this function doesn't exist.
    document.elementFromPoint = () => null
  })

  it('Should call focusDialogEntry on quote click with quote index', async () => {
    const focusDialogEntry = vi.fn()

    render(
      <SimpleEditor
        initialContent={'test content[1]'}
        onContentChange={() => null}
        isEditing={false}
        currentTranscription={{} as TranscriptionGetResponse}
        hideCitations={false}
        focusDialogEntry={focusDialogEntry}
      />
    )

    const citationLink = screen.getByText('[1]')
    expect(citationLink).toBeInTheDocument()

    await userEvent.click(citationLink)
    expect(focusDialogEntry).toHaveBeenCalledWith(1)
  })
})
