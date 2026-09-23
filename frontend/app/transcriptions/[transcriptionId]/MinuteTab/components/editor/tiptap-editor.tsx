'use client'

import { Extension, Node, mergeAttributes } from '@tiptap/core'
import type { Editor } from '@tiptap/react'
import { EditorContent, useEditor, useEditorState } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import type { NodeType } from 'prosemirror-model'
import { EditorState, Plugin, PluginKey } from 'prosemirror-state'
import { Decoration, DecorationSet } from 'prosemirror-view'
import type { EditorView } from 'prosemirror-view'
import { useCallback, useEffect } from 'react'

import { citationRegexWithSpace } from '@/lib/citationRegex'
import { TranscriptionGetResponse } from '@/lib/client'
import { cn } from '@/lib/utils'
import posthog from 'posthog-js'
import {
  Bold as BoldIcon,
  Code as CodeIcon,
  Italic as ItalicIcon,
  ListOrdered as OrderedListIcon,
  RotateLeft,
  RotateRight,
  Strikethrough as StrikethroughIcon,
  List as UnorderedListIcon,
} from './Icons'

function SimpleEditor({
  initialContent,
  onContentChange,
  isEditing,
  currentTranscription,
  hideCitations,
  onCitationClicked,
}: {
  initialContent: string
  onContentChange: (newContent: string) => void
  isEditing: boolean
  currentTranscription: TranscriptionGetResponse
  hideCitations: boolean
  onCitationClicked?: (citationIndex: number) => void
}) {
  const CitationNode = Node.create({
    name: 'citationNode',
    group: 'inline',
    inline: true,
    atom: true,
    selectable: false,
    addAttributes() {
      return {
        citationIndex: {
          default: null,
          parseHTML: (element) => {
            const attr = element.getAttribute('data-citation-index')
            if (attr !== null) return attr
            const match = element.textContent?.match(/\[(\d+)(?:-\d+)?\]/)
            return match ? match[1] : null
          },
          renderHTML: (attributes) => {
            if (attributes.citationIndex === null) return {}
            return { 'data-citation-index': attributes.citationIndex }
          },
        },

        label: {
          default: null,
          parseHTML: (element) => element.textContent || null,
          renderHTML: () => ({}),
        },
      }
    },
    parseHTML() {
      return [{ tag: 'span[data-citation]' }]
    },
    renderHTML({ node, HTMLAttributes }) {
      const citationIndex = node.attrs.citationIndex as string | null
      const label =
        (node.attrs.label as string | null) ??
        (citationIndex !== null ? `[${citationIndex}]` : '[citation]')
      return [
        'span',
        mergeAttributes(HTMLAttributes, {
          'data-citation': 'true',
          class: 'citation-link',
          style:
            'color: blue; cursor: pointer; text-decoration: underline; display: var(--citation-display);',
          role: 'button',
          tabindex: '0',
          'aria-label': citationIndex
            ? `View citation ${citationIndex} in transcript`
            : 'View citation in transcript',
        }),
        label,
      ]
    },
  })

  const seedCitationNodes = (view: EditorView, nodeType: NodeType) => {
    const { state } = view
    const tr = state.tr
    let changed = false

    state.doc.descendants((node, pos) => {
      if (!node.isText || !node.text) return

      const regex = new RegExp(citationRegexWithSpace.source, 'g')
      let match
      while ((match = regex.exec(node.text)) !== null) {
        const from = pos + match.index + match[1].length
        const to = pos + match.index + match[0].length
        const citationIndex = match[2]
        const label = node.text.slice(
          match.index + match[1].length,
          match.index + match[0].length
        )

        const mappedFrom = tr.mapping.map(from, -1)
        const mappedTo = tr.mapping.map(to, 1)

        tr.replaceWith(
          mappedFrom,
          mappedTo,
          nodeType.create({ citationIndex, label })
        )
        changed = true
      }
    })

    if (changed) {
      tr.setMeta('addToHistory', false)
      view.dispatch(tr)
    }
  }

  const CitationExtension = Extension.create({
    name: 'citation',
    addProseMirrorPlugins() {
      const activateCitation = (domNode: HTMLElement): boolean => {
        const citationLink = domNode.closest<HTMLElement>('.citation-link')
        if (!citationLink) return false
        const indexAttr = citationLink.getAttribute('data-citation-index')
        if (indexAttr === null) return false
        const index = parseInt(indexAttr, 10)
        posthog.capture('citation_clicked', { citationIndex: index })
        onCitationClicked?.(index)
        return true
      }

      return [
        new Plugin({
          key: new PluginKey('citation'),
          props: {
            decorations(state) {
              const decorations: Decoration[] = []
              const nodeType = state.schema.nodes.citationNode
              const dialogueEntryCount =
                currentTranscription.dialogue_entries?.length ?? 0

              state.doc.descendants((node, pos) => {
                if (node.type !== nodeType) return

                const citationIndex = node.attrs.citationIndex as string | null
                const index =
                  citationIndex !== null ? parseInt(citationIndex, 10) : NaN
                const isValid =
                  !Number.isNaN(index) && index < dialogueEntryCount

                const charBefore =
                  pos > 0 ? state.doc.textBetween(pos - 1, pos) : ''
                const hasLeadingSpace = /\s/.test(charBefore)

                if (!isValid) {
                  decorations.push(
                    Decoration.node(pos, pos + node.nodeSize, {
                      style: 'display: none',
                    })
                  )
                  if (hasLeadingSpace) {
                    decorations.push(
                      Decoration.inline(pos - 1, pos, {
                        style: 'display: none',
                      })
                    )
                  }
                  return
                }

                if (hasLeadingSpace) {
                  decorations.push(
                    Decoration.inline(pos - 1, pos, {
                      style: 'display: var(--citation-display);',
                    })
                  )
                }
              })

              return DecorationSet.create(state.doc, decorations)
            },
            handleKeyDown(view, event) {
              if (event.key !== 'Backspace' && event.key !== 'Delete') {
                return false
              }

              const { state } = view
              const { selection } = state
              if (!selection.empty) return false

              const pos = selection.from
              const nodeType = state.schema.nodes.citationNode

              if (event.key === 'Backspace') {
                const before = state.doc.nodeAt(pos - 1)
                if (before?.type === nodeType) {
                  view.dispatch(state.tr.delete(pos - before.nodeSize, pos))
                  event.preventDefault()
                  return true
                }
              }

              if (event.key === 'Delete') {
                const after = state.doc.nodeAt(pos)
                if (after?.type === nodeType) {
                  view.dispatch(state.tr.delete(pos, pos + after.nodeSize))
                  event.preventDefault()
                  return true
                }
              }

              return false
            },
            handleDOMEvents: {
              click: (_view, event) => {
                return activateCitation(event.target as HTMLElement)
              },

              keydown: (_view, event) => {
                if (event.key !== 'Enter' && event.key !== ' ') return false
                const activated = activateCitation(event.target as HTMLElement)
                if (activated) event.preventDefault()
                return activated
              },
            },
          },
        }),
      ]
    },
  })

  const editorObject = useEditor({
    extensions: [StarterKit, CitationNode, CitationExtension],
    onCreate: ({ editor }) => {
      seedCitationNodes(editor.view, editor.schema.nodes.citationNode)
    },
    onUpdate: ({ editor }) => {
      onContentChange(editor.getHTML())
    },
    immediatelyRender: false,
    content: initialContent,
  }) as Editor

  useEffect(() => {
    if (editorObject) {
      editorObject.setEditable(isEditing)
    }
  }, [editorObject, isEditing])

  useEffect(() => {
    if (editorObject && initialContent !== editorObject.getHTML()) {
      editorObject.commands.setContent(initialContent, { emitUpdate: false })
      seedCitationNodes(
        editorObject.view,
        editorObject.schema.nodes.citationNode
      )
      const newEditorState = EditorState.create({
        doc: editorObject.state.doc,
        plugins: editorObject.state.plugins,
        schema: editorObject.state.schema,
      })
      editorObject.view.updateState(newEditorState)
    }
  }, [editorObject, initialContent])

  const toggleBold = useCallback(() => {
    editorObject.chain().focus().toggleBold().run()
  }, [editorObject])

  const toggleItalic = useCallback(() => {
    editorObject.chain().focus().toggleItalic().run()
  }, [editorObject])

  const toggleStrike = useCallback(() => {
    editorObject.chain().focus().toggleStrike().run()
  }, [editorObject])

  const toggleCode = useCallback(() => {
    editorObject.chain().focus().toggleCode().run()
  }, [editorObject])

  const toggleBulletList = useCallback(() => {
    editorObject.chain().focus().toggleBulletList().run()
  }, [editorObject])

  const toggleOrderedList = useCallback(() => {
    editorObject.chain().focus().toggleOrderedList().run()
  }, [editorObject])

  const editorState = useEditorState({
    editor: editorObject,
    selector: (snapshot) => ({
      isBoldActive: snapshot?.editor?.isActive('bold'),
      isItalicActive: snapshot?.editor?.isActive('italic'),
      isStrikeActive: snapshot?.editor?.isActive('strike'),
      isCodeActive: snapshot?.editor?.isActive('code'),
      isHeading3Active: snapshot?.editor?.isActive('heading', { level: 3 }),
      isBulletListActive: snapshot?.editor?.isActive('bulletList'),
      isOrderedListActive: snapshot?.editor?.isActive('orderedList'),
      undoAvailable: snapshot?.editor?.can().chain().focus().undo().run(),
      redoAvailable: snapshot?.editor?.can().chain().focus().redo().run(),
    }),
  })

  if (!editorObject || !editorState) {
    return null
  }

  return (
    <div className="relative rounded-md border border-gray-300">
      {isEditing && (
        <div className="flex items-center justify-between border-b border-gray-300 bg-gray-50 p-2">
          <div className="flex items-center">
            <div className="mr-4 flex space-x-1">
              <button
                aria-label="Undo"
                className="rounded p-1 hover:bg-gray-200 disabled:opacity-50"
                onClick={() => editorObject.chain().focus().undo().run()}
                disabled={!editorState.undoAvailable}
                type="button"
              >
                <RotateLeft size={20} />
              </button>
              <button
                aria-label="Redo"
                className="rounded p-1 hover:bg-gray-200 disabled:opacity-50"
                onClick={() => editorObject.chain().focus().redo().run()}
                disabled={!editorState.redoAvailable}
                type="button"
              >
                <RotateRight size={20} />
              </button>
            </div>
            <div className="mr-4 flex space-x-1">
              <button
                aria-label="Bold"
                aria-pressed={editorState.isBoldActive}
                className={cn('rounded p-1 hover:bg-gray-200', {
                  'bg-gray-300': editorState.isBoldActive,
                })}
                onClick={toggleBold}
                type="button"
              >
                <BoldIcon size={20} />
              </button>
              <button
                aria-label="Italic"
                aria-pressed={editorState.isItalicActive}
                className={cn('rounded p-1 hover:bg-gray-200', {
                  'bg-gray-300': editorState.isItalicActive,
                })}
                onClick={toggleItalic}
                type="button"
              >
                <ItalicIcon size={20} />
              </button>

              <button
                aria-label="Strikethrough"
                aria-pressed={editorState.isStrikeActive}
                className={cn('rounded p-1 hover:bg-gray-200', {
                  'bg-gray-300': editorState.isStrikeActive,
                })}
                onClick={toggleStrike}
                type="button"
              >
                <StrikethroughIcon size={20} />
              </button>
            </div>
            <div className="mr-4 flex space-x-1">
              <button
                aria-label="Code"
                aria-pressed={editorState.isCodeActive}
                className={cn('rounded p-1 hover:bg-gray-200', {
                  'bg-gray-300': editorState.isCodeActive,
                })}
                onClick={toggleCode}
                type="button"
              >
                <CodeIcon size={20} />
              </button>
            </div>
            <div className="flex space-x-1">
              <button
                aria-label="Bullet list"
                aria-pressed={editorState.isBulletListActive}
                className={cn('rounded p-1 hover:bg-gray-200', {
                  'bg-gray-300': editorState.isBulletListActive,
                })}
                onClick={toggleBulletList}
                type="button"
              >
                <UnorderedListIcon size={20} />
              </button>
              <button
                aria-label="Numbered list"
                aria-pressed={editorState.isOrderedListActive}
                className={cn('rounded p-1 hover:bg-gray-200', {
                  'bg-gray-300': editorState.isOrderedListActive,
                })}
                onClick={toggleOrderedList}
                type="button"
              >
                <OrderedListIcon size={20} />
              </button>
              <button
                aria-label="Heading 3"
                aria-pressed={editorState.isHeading3Active}
                className={cn('rounded p-1 hover:bg-gray-200', {
                  'bg-gray-300': editorState.isHeading3Active,
                })}
                onClick={() =>
                  editorObject.chain().focus().toggleHeading({ level: 3 }).run()
                }
                type="button"
              >
                H3
              </button>
            </div>
          </div>
        </div>
      )}

      <EditorContent
        editor={editorObject}
        className={cn('editor-content')}
        style={
          {
            '--citation-display': hideCitations ? 'none' : 'unset',
          } as React.CSSProperties
        }
      />
    </div>
  )
}

export default SimpleEditor
