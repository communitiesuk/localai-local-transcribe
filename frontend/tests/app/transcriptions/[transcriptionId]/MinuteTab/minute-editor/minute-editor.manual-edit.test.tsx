import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MinuteEditor } from '@/app/transcriptions/[transcriptionId]/MinuteTab/minute-editor/minute-editor'
import {
  Minute,
  MinuteVersionResponse,
  TranscriptionGetResponse,
} from '@/lib/client'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

const versions: MinuteVersionResponse[] = [
  {
    id: 'v1',
    status: 'completed',
    content_source: 'initial_generation',
    created_datetime: '2024-01-01T00:00:00Z',
    html_content: 'Generated version content',
  } as MinuteVersionResponse,
]

vi.mock('@/lib/client/@tanstack/react-query.gen', () => ({
  listMinuteVersionsMinutesMinuteIdVersionsGetOptions: () => ({
    queryKey: ['versions'],
  }),
  listMinuteVersionsMinutesMinuteIdVersionsGetQueryKey: () => ['versions'],
  createMinuteVersionMinutesMinuteIdVersionsPostMutation: () => ({
    mutationKey: ['create-minute-version'],
  }),
  deleteMinuteVersionMinuteVersionsMinuteVersionIdDeleteMutation: () => ({
    mutationKey: ['delete-minute-version'],
  }),
}))

// Stub the rich text editor; like the real one it only reads initialContent on mount.
vi.mock(
  '@/app/transcriptions/[transcriptionId]/MinuteTab/components/editor/tiptap-editor',
  async () => {
    const { useState } = await vi.importActual<typeof import('react')>('react')
    return {
      default: function StubEditor({
        initialContent,
        onContentChange,
      }: {
        initialContent: string
        onContentChange: (content: string) => void
      }) {
        const [content, setContent] = useState(initialContent)
        return (
          <div>
            <div>{content}</div>
            <button
              type="button"
              onClick={() => {
                setContent('edited content')
                onContentChange('edited content')
              }}
            >
              stub-change-content
            </button>
          </div>
        )
      },
    }
  }
)

// Stub the AI edit popover to keep this test focused on the toolbar.
vi.mock(
  '@/app/transcriptions/[transcriptionId]/MinuteTab/minute-editor/ai-edit-popover',
  () => ({
    AiEditPopover: ({ disabled }: { disabled?: boolean }) => (
      <button type="button" disabled={disabled}>
        AI edit
      </button>
    ),
  })
)

vi.mock('@tanstack/react-query', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@tanstack/react-query')>()
  return {
    ...actual,
    useQuery: vi.fn(),
    useMutation: vi.fn(),
    useQueryClient: vi.fn(),
  }
})

beforeEach(() => {
  vi.clearAllMocks()
  vi.mocked(useQuery).mockReturnValue({
    data: versions,
    isLoading: false,
    isError: false,
    refetch: vi.fn(),
  } as unknown as ReturnType<typeof useQuery>)
  vi.mocked(useMutation).mockReturnValue({
    mutate: vi.fn(),
    isPending: false,
  } as unknown as ReturnType<typeof useMutation>)
  vi.mocked(useQueryClient).mockReturnValue({
    invalidateQueries: vi.fn(),
  } as unknown as ReturnType<typeof useQueryClient>)
})

const renderEditor = () =>
  render(
    <MinuteEditor
      transcription={
        {
          id: 't1',
          dialogue_entries: [],
        } as unknown as TranscriptionGetResponse
      }
      minute={{ id: 'm1' } as Minute}
    />
  )

describe('<MinuteEditor /> manual edit mode', () => {
  it('disables the toolbar controls and shows Save/Cancel edits when editing starts', () => {
    renderEditor()

    fireEvent.click(screen.getByRole('button', { name: 'Manual edit' }))

    expect(screen.getByRole('button', { name: 'Manual edit' })).toBeDisabled()
    expect(
      screen.getByRole('button', { name: 'Download document' })
    ).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Copy document' })).toBeDisabled()
    expect(screen.getByLabelText('Version history')).toBeDisabled()
    expect(
      screen.getByRole('button', { name: 'Save edits' })
    ).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: 'Cancel edits' })
    ).toBeInTheDocument()
  })

  it('opens the discard modal when cancelling with unsaved changes', () => {
    renderEditor()

    fireEvent.click(screen.getByRole('button', { name: 'Manual edit' }))
    fireEvent.click(screen.getByRole('button', { name: 'stub-change-content' }))
    fireEvent.click(screen.getByRole('button', { name: 'Cancel edits' }))

    expect(
      screen.getByText('Are you sure you want to discard your changes?')
    ).toBeInTheDocument()
  })

  it('exits edit mode with no modal when cancelling with no changes', () => {
    renderEditor()

    fireEvent.click(screen.getByRole('button', { name: 'Manual edit' }))
    fireEvent.click(screen.getByRole('button', { name: 'Cancel edits' }))

    expect(
      screen.queryByText('Are you sure you want to discard your changes?')
    ).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Manual edit' })).toBeEnabled()
  })

  it('restores the original content when changes are discarded', () => {
    renderEditor()

    fireEvent.click(screen.getByRole('button', { name: 'Manual edit' }))
    fireEvent.click(screen.getByRole('button', { name: 'stub-change-content' }))
    expect(screen.getByText('edited content')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Cancel edits' }))
    fireEvent.click(screen.getByRole('button', { name: 'Discard' }))

    expect(screen.getByText('Generated version content')).toBeInTheDocument()
    expect(screen.queryByText('edited content')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Manual edit' })).toBeEnabled()
  })
})
