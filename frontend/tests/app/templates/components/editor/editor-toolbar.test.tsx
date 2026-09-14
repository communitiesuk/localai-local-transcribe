import { TemplateEditorToolbar } from '@/app/templates/components/editor/editor-toolbar'
import { Editor } from '@tiptap/core'
import StarterKit from '@tiptap/starter-kit'
import { act, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'

describe('<TemplateEditorToolbar />', () => {
  let editor: Editor

  beforeEach(() => {
    editor = new Editor({
      extensions: [StarterKit],
      content: '<p><strong>Bold</strong> plain</p>',
    })
  })

  afterEach(() => {
    editor.destroy()
  })

  it('updates the active formatting state when the selection moves', async () => {
    editor.commands.setTextSelection(7)
    render(<TemplateEditorToolbar editor={editor} />)

    const boldButton = screen.getByRole('button', { name: 'Bold' })
    expect(boldButton).toHaveAttribute('aria-pressed', 'false')

    act(() => {
      editor.commands.setTextSelection(2)
    })

    await waitFor(() => {
      expect(boldButton).toHaveAttribute('aria-pressed', 'true')
    })
  })

  it('updates undo and redo availability after transactions', async () => {
    render(<TemplateEditorToolbar editor={editor} />)

    const undoButton = screen.getByRole('button', { name: 'Undo' })
    const redoButton = screen.getByRole('button', { name: 'Redo' })

    expect(undoButton).toBeDisabled()
    expect(redoButton).toBeDisabled()

    act(() => {
      editor.commands.insertContent('Changed')
    })

    await waitFor(() => {
      expect(undoButton).toBeEnabled()
    })

    act(() => {
      editor.commands.undo()
    })

    await waitFor(() => {
      expect(redoButton).toBeEnabled()
    })
  })
})
