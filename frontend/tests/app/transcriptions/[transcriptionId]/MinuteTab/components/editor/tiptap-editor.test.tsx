import SimpleEditor from '@/app/transcriptions/[transcriptionId]/MinuteTab/components/editor/tiptap-editor'
import { DialogueEntry, TranscriptionGetResponse } from '@/lib/client'
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeAll, describe, expect, it, vi } from 'vitest'

const transcription = {
  id: 'transcription-1',
} as TranscriptionGetResponse

const dialogueEntry = (index: number): DialogueEntry => ({
  speaker: `Speaker ${index}`,
  text: `Entry ${index}`,
  start_time: index,
  end_time: index + 1,
})

const transcriptionWithEntries: TranscriptionGetResponse = {
  id: 'transcription-1',
  title: null,
  dialogue_entries: [dialogueEntry(0), dialogueEntry(1)],
  status: 'completed',
  created_datetime: '2024-01-01T00:00:00Z',
  client_name: null,
  case_id: null,
  client_date_of_birth: null,
}

const citationProps = {
  currentTranscription: transcriptionWithEntries,
  hideCitations: false,
}

const defaultProps = {
  currentTranscription: transcription,
  hideCitations: false,
  isEditing: true,
}

const placeCaret = (textNode: Text, offset: number) => {
  const range = document.createRange()
  range.setStart(textNode, offset)
  range.collapse(true)

  const selection = window.getSelection()
  if (!selection) {
    throw new Error('Selection API is unavailable')
  }

  selection.removeAllRanges()
  selection.addRange(range)
  fireEvent(document, new Event('selectionchange'))
}

describe('<SimpleEditor />', () => {
  it('updates toolbar state when the caret moves through formatted text', async () => {
    const { container } = render(
      <SimpleEditor
        {...defaultProps}
        initialContent="<p><strong>Bold text</strong> plain text</p>"
        onContentChange={vi.fn()}
      />
    )

    const editable = await waitFor(() => {
      const element = container.querySelector<HTMLElement>('.ProseMirror')
      expect(element).not.toBeNull()
      return element!
    })
    const boldText = editable.querySelector('strong')?.firstChild
    const plainText = editable.querySelector('p')?.lastChild

    expect(boldText).toBeInstanceOf(Text)
    expect(plainText).toBeInstanceOf(Text)

    const boldButton = screen.getByRole('button', { name: 'Bold' })

    act(() => {
      editable.focus()
      placeCaret(plainText as Text, 2)
    })

    await waitFor(() => {
      expect(boldButton).toHaveAttribute('aria-pressed', 'false')
    })

    act(() => {
      placeCaret(boldText as Text, 2)
    })

    await waitFor(() => {
      expect(boldButton).toHaveAttribute('aria-pressed', 'true')
    })

    act(() => {
      placeCaret(plainText as Text, 2)
    })

    await waitFor(() => {
      expect(boldButton).toHaveAttribute('aria-pressed', 'false')
    })
  })

  it('does not report prop-driven content changes as user edits', async () => {
    const onContentChange = vi.fn()
    const { container, rerender } = render(
      <SimpleEditor
        {...defaultProps}
        initialContent="<p>First version</p>"
        onContentChange={onContentChange}
      />
    )

    await waitFor(() => {
      expect(container.querySelector('.ProseMirror')).toHaveTextContent(
        'First version'
      )
    })
    onContentChange.mockClear()

    rerender(
      <SimpleEditor
        {...defaultProps}
        initialContent="<p>Second version</p>"
        onContentChange={onContentChange}
      />
    )

    await waitFor(() => {
      expect(container.querySelector('.ProseMirror')).toHaveTextContent(
        'Second version'
      )
    })
    expect(onContentChange).not.toHaveBeenCalled()
  })
})

describe('<SimpleEditor /> citation behaviour', () => {
  beforeAll(() => {
    document.elementFromPoint = () => null
    Range.prototype.getClientRects = () =>
      ({ length: 0, item: () => null }) as unknown as DOMRectList
    Range.prototype.getBoundingClientRect = () =>
      ({ top: 0, left: 0, right: 0, bottom: 0, width: 0, height: 0 }) as DOMRect
  })

  it('activates a citation on click', async () => {
    const onCitationClicked = vi.fn()
    render(
      <SimpleEditor
        {...citationProps}
        isEditing={true}
        initialContent="<p>See [0] for details</p>"
        onContentChange={vi.fn()}
        onCitationClicked={onCitationClicked}
      />
    )
    const citation = await waitFor(() => screen.getByText('[0]'))
    await userEvent.click(citation)
    expect(onCitationClicked).toHaveBeenCalledWith(0)
  })

  it.each([true, false])(
    'activates a citation via Enter when isEditing=%s',
    async (isEditing) => {
      const onCitationClicked = vi.fn()
      render(
        <SimpleEditor
          {...citationProps}
          isEditing={isEditing}
          initialContent="<p>See [0] for details</p>"
          onContentChange={vi.fn()}
          onCitationClicked={onCitationClicked}
        />
      )
      const citation = await waitFor(() => screen.getByText('[0]'))
      citation.focus()
      fireEvent.keyDown(citation, { key: 'Enter', code: 'Enter' })
      expect(onCitationClicked).toHaveBeenCalledWith(0)
    }
  )

  it('exposes each citation as a focusable, labelled control', async () => {
    render(
      <SimpleEditor
        {...citationProps}
        isEditing={true}
        initialContent="<p>See [0] for details</p>"
        onContentChange={vi.fn()}
      />
    )
    const citation = await waitFor(() => screen.getByText('[0]'))
    expect(citation).toHaveAttribute('role', 'button')
    expect(citation).toHaveAttribute('tabindex', '0')
    expect(citation).toHaveAttribute(
      'aria-label',
      'View citation 0 in transcript'
    )
  })

  it('hides a citation with no matching transcript entry', async () => {
    const { container } = render(
      <SimpleEditor
        {...citationProps}
        isEditing={true}
        initialContent="<p>Valid [0] invalid [5]</p>"
        onContentChange={vi.fn()}
      />
    )
    await waitFor(() => {
      expect(container.querySelector('.ProseMirror')).toHaveTextContent('Valid')
    })
    expect(screen.getByText('[0]')).toBeVisible()
    expect(screen.getByText('[5]')).not.toBeVisible()
  })

  it('deletes a whole citation with a single Backspace at its end', async () => {
    const { container } = render(
      <SimpleEditor
        {...citationProps}
        isEditing={true}
        initialContent="<p>Ref [0] end</p>"
        onContentChange={vi.fn()}
      />
    )
    const editable = await waitFor(() => {
      const element = container.querySelector<HTMLElement>('.ProseMirror')
      expect(element).not.toBeNull()
      return element!
    })
    const citation = screen.getByText('[0]')
    const textNode = citation.firstChild as Text

    act(() => {
      editable.focus()
      placeCaret(textNode, textNode.data.length)
    })

    fireEvent.keyDown(editable, { key: 'Backspace', code: 'Backspace' })

    await waitFor(() => {
      expect(screen.queryByText('[0]')).not.toBeInTheDocument()
    })
    expect(editable).toHaveTextContent('Ref end')
  })

  it('keeps adjacent citations independently indexed and clickable', async () => {
    const onCitationClicked = vi.fn()
    render(
      <SimpleEditor
        {...citationProps}
        isEditing={true}
        initialContent="<p>[0][1]</p>"
        onContentChange={vi.fn()}
        onCitationClicked={onCitationClicked}
      />
    )
    const first = await waitFor(() => screen.getByText('[0]'))
    const second = screen.getByText('[1]')

    expect(first).toHaveAttribute('data-citation-index', '0')
    expect(second).toHaveAttribute('data-citation-index', '1')

    await userEvent.click(first)
    expect(onCitationClicked).toHaveBeenLastCalledWith(0)

    await userEvent.click(second)
    expect(onCitationClicked).toHaveBeenLastCalledWith(1)
  })
})
