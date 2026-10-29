'use client'

import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Editor } from '@tiptap/core'
import { useEditorState } from '@tiptap/react'
import {
  Bold,
  Code,
  Heading1,
  Heading2,
  Heading3,
  Heading4,
  Italic,
  List,
  ListOrdered,
  Redo,
  Strikethrough,
  Undo,
} from 'lucide-react'

interface TemplateEditorToolbarProps {
  editor: Editor | null
}

export const TemplateEditorToolbar = ({
  editor,
}: TemplateEditorToolbarProps) => {
  const editorState = useEditorState({
    editor,
    selector: (snapshot) => ({
      isBoldActive: snapshot?.editor?.isActive('bold'),
      isItalicActive: snapshot?.editor?.isActive('italic'),
      isStrikeActive: snapshot?.editor?.isActive('strike'),
      isCodeActive: snapshot?.editor?.isActive('code'),
      isHeading1Active: snapshot?.editor?.isActive('heading', { level: 1 }),
      isHeading2Active: snapshot?.editor?.isActive('heading', { level: 2 }),
      isHeading3Active: snapshot?.editor?.isActive('heading', { level: 3 }),
      isHeading4Active: snapshot?.editor?.isActive('heading', { level: 4 }),
      isBulletListActive: snapshot?.editor?.isActive('bulletList'),
      isOrderedListActive: snapshot?.editor?.isActive('orderedList'),
      undoAvailable: snapshot?.editor?.can().chain().focus().undo().run(),
      redoAvailable: snapshot?.editor?.can().chain().focus().redo().run(),
    }),
  })

  if (!editor || !editorState) {
    return null
  }

  return (
    <Card className="rounded-none border-x-0 border-t-0 border-b p-2 shadow-none">
      <div className="flex flex-wrap gap-1">
        <Button
          type="button"
          aria-label="Bold"
          aria-pressed={editorState.isBoldActive}
          variant={editorState.isBoldActive ? 'secondary' : 'ghost'}
          size="sm"
          onClick={() => editor.chain().focus().toggleBold().run()}
        >
          <Bold />
        </Button>
        <Button
          type="button"
          aria-label="Italic"
          aria-pressed={editorState.isItalicActive}
          variant={editorState.isItalicActive ? 'secondary' : 'ghost'}
          size="sm"
          onClick={() => editor.chain().focus().toggleItalic().run()}
        >
          <Italic />
        </Button>
        <Button
          type="button"
          aria-label="Strikethrough"
          aria-pressed={editorState.isStrikeActive}
          variant={editorState.isStrikeActive ? 'secondary' : 'ghost'}
          size="sm"
          onClick={() => editor.chain().focus().toggleStrike().run()}
        >
          <Strikethrough />
        </Button>
        <Button
          type="button"
          aria-label="Code"
          aria-pressed={editorState.isCodeActive}
          variant={editorState.isCodeActive ? 'secondary' : 'ghost'}
          size="sm"
          onClick={() => editor.chain().focus().toggleCode().run()}
        >
          <Code />
        </Button>
        <div className="mx-1 h-6 w-px bg-gray-300" />
        <Button
          type="button"
          aria-label="Heading 1"
          aria-pressed={editorState.isHeading1Active}
          variant={editorState.isHeading1Active ? 'secondary' : 'ghost'}
          size="sm"
          onClick={() =>
            editor.chain().focus().toggleHeading({ level: 1 }).run()
          }
        >
          <Heading1 />
        </Button>
        <Button
          type="button"
          aria-label="Heading 2"
          aria-pressed={editorState.isHeading2Active}
          variant={editorState.isHeading2Active ? 'secondary' : 'ghost'}
          size="sm"
          onClick={() =>
            editor.chain().focus().toggleHeading({ level: 2 }).run()
          }
        >
          <Heading2 />
        </Button>
        <Button
          type="button"
          aria-label="Heading 3"
          aria-pressed={editorState.isHeading3Active}
          variant={editorState.isHeading3Active ? 'secondary' : 'ghost'}
          size="sm"
          onClick={() =>
            editor.chain().focus().toggleHeading({ level: 3 }).run()
          }
        >
          <Heading3 />
        </Button>
        <Button
          type="button"
          aria-label="Heading 4"
          aria-pressed={editorState.isHeading4Active}
          variant={editorState.isHeading4Active ? 'secondary' : 'ghost'}
          size="sm"
          onClick={() =>
            editor.chain().focus().toggleHeading({ level: 4 }).run()
          }
        >
          <Heading4 />
        </Button>
        <div className="mx-1 h-6 w-px bg-gray-300" />
        <Button
          type="button"
          aria-label="Bullet list"
          aria-pressed={editorState.isBulletListActive}
          variant={editorState.isBulletListActive ? 'secondary' : 'ghost'}
          size="sm"
          onClick={() => editor.chain().focus().toggleBulletList().run()}
        >
          <List />
        </Button>
        <Button
          type="button"
          aria-label="Numbered list"
          aria-pressed={editorState.isOrderedListActive}
          variant={editorState.isOrderedListActive ? 'secondary' : 'ghost'}
          size="sm"
          onClick={() => editor.chain().focus().toggleOrderedList().run()}
        >
          <ListOrdered />
        </Button>
        <div className="mx-1 h-6 w-px bg-gray-300" />
        <Button
          type="button"
          aria-label="Undo"
          variant="ghost"
          size="sm"
          onClick={() => editor.chain().focus().undo().run()}
          disabled={!editorState.undoAvailable}
        >
          <Undo />
        </Button>
        <Button
          type="button"
          aria-label="Redo"
          variant="ghost"
          size="sm"
          onClick={() => editor.chain().focus().redo().run()}
          disabled={!editorState.redoAvailable}
        >
          <Redo />
        </Button>
      </div>
    </Card>
  )
}
