import SimpleEditor from '@/app/transcriptions/[transcriptionId]/MinuteTab/components/editor/tiptap-editor'
import { TranscriptionGetResponse } from '@/lib/client'
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

const transcription = {
  id: 'transcription-1',
} as TranscriptionGetResponse

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
