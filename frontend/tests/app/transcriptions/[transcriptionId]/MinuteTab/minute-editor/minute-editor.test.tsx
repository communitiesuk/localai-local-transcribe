import { render, screen, fireEvent } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { MinuteEditor } from '@/app/transcriptions/[transcriptionId]/MinuteTab/minute-editor/minute-editor'
import type {
  MinuteListItem,
  MinuteVersionResponse,
  TranscriptionGetResponse,
} from '@/lib/client'

vi.mock('posthog-js', () => ({ default: { capture: vi.fn() } }))

vi.mock(
  '@/app/transcriptions/[transcriptionId]/MinuteTab/components/editor/tiptap-editor',
  () => ({
    default: ({
      initialContent,
    }: {
      initialContent: string
      onContentChange: (v: string) => void
    }) => <div data-testid="simple-editor">{initialContent}</div>,
  })
)

vi.mock('@/lib/client/@tanstack/react-query.gen', () => ({
  createMinuteVersionMinutesMinuteIdVersionsPostMutation: () => ({
    mutationKey: ['create-minute-version'],
  }),
  deleteMinuteVersionMinuteVersionsMinuteVersionIdDeleteMutation: () => ({
    mutationKey: ['delete-minute-version'],
  }),
  listMinuteVersionsMinutesMinuteIdVersionsGetOptions: () => ({
    queryKey: ['minute-versions'],
  }),
  listMinuteVersionsMinutesMinuteIdVersionsGetQueryKey: () => [
    'minute-versions',
  ],
  createMinuteTranscriptionTranscriptionIdMinutesPostMutation: () => ({
    mutationKey: ['create-minute'],
  }),
}))

vi.mock('@tanstack/react-query', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@tanstack/react-query')>()
  return {
    ...actual,
    useQuery: vi.fn(),
    useMutation: vi.fn(),
    useQueryClient: vi.fn(),
  }
})

const setBannerMock = vi.fn()
vi.mock('@/stores/use-banner-store', () => ({
  useBannerStore: () => ({ setBanner: setBannerMock }),
}))

const transcription = {
  id: 'transcription-1',
  dialogue_entries: [],
  title: 'Meeting',
} as unknown as TranscriptionGetResponse

const minute = {
  id: 'minute-1',
  template_name: 'General summary',
  agenda: null,
} as unknown as MinuteListItem

const makeVersion = (
  overrides: Partial<MinuteVersionResponse> = {}
): MinuteVersionResponse =>
  ({
    id: 'v1',
    minute_id: 'minute-1',
    status: 'completed',
    created_datetime: '2024-01-01T00:00:00Z',
    html_content: '<p>content</p>',
    error: null,
    ai_edit_instructions: null,
    content_source: 'initial_generation',
    ...overrides,
  }) as MinuteVersionResponse

const mutateMock = vi.fn()
const deleteMutateMock = vi.fn()
const invalidateQueriesMock = vi.fn()

const configureQuery = (data: MinuteVersionResponse[], isLoading = false) => {
  vi.mocked(useQuery).mockReturnValue({
    data,
    isLoading,
  } as unknown as ReturnType<typeof useQuery>)
}

const renderEditor = () =>
  render(<MinuteEditor transcription={transcription} minute={minute} />)

beforeEach(() => {
  vi.clearAllMocks()
  vi.mocked(useMutation).mockReturnValue({
    mutate: mutateMock,
    isPending: false,
  } as unknown as ReturnType<typeof useMutation>)
  vi.mocked(useQueryClient).mockReturnValue({
    invalidateQueries: invalidateQueriesMock,
  } as unknown as ReturnType<typeof useQueryClient>)
})

describe('<MinuteEditor /> AI edit flow', () => {
  it('shows a loading state while versions are loading', () => {
    configureQuery([], true)
    renderEditor()
    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  it('prompts to generate a minute when no versions exist', () => {
    configureQuery([])
    renderEditor()
    expect(
      screen.getByText(/There has been an error loading this document/)
    ).toBeInTheDocument()
  })

  it('shows the AI-edit specific spinner while an AI edit is in progress', () => {
    configureQuery([
      makeVersion({
        id: 'v2',
        status: 'in_progress',
        content_source: 'ai_edit',
      }),
      makeVersion({ id: 'v1' }),
    ])
    renderEditor()

    expect(
      screen.getByText(`Applying AI edits to ‘General summary’…`)
    ).toBeInTheDocument()
    expect(screen.queryByText('Minute generating...')).not.toBeInTheDocument()
  })

  it('shows the generic pulse loader for a non-AI-edit generation', () => {
    configureQuery([
      makeVersion({
        id: 'v1',
        status: 'in_progress',
        content_source: 'initial_generation',
      }),
    ])
    renderEditor()

    expect(screen.getByText('Minute generating...')).toBeInTheDocument()
  })

  it('shows the completed AI-edited document and the AI Edit button once done', () => {
    configureQuery([
      makeVersion({ id: 'v2', status: 'completed', content_source: 'ai_edit' }),
      makeVersion({ id: 'v1' }),
    ])
    renderEditor()

    expect(screen.getByTestId('simple-editor')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'AI Edit' })).toBeInTheDocument()
  })

  it('renders an inline error banner with an Undo action when explicitly viewing a failed version', () => {
    configureQuery([
      makeVersion({ id: 'v2', status: 'failed', content_source: 'ai_edit' }),
      makeVersion({ id: 'v1' }),
    ])
    renderEditor()

    fireEvent.change(
      screen.getByRole('combobox', { name: 'Version history' }),
      {
        target: { value: 'v2' },
      }
    )

    expect(screen.getByText('There is a problem')).toBeInTheDocument()
    expect(
      screen.getByText(
        'There was a problem processing your request. Click undo to go back to the previous version.'
      )
    ).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Undo/ })).toBeInTheDocument()
  })

  it('shows the "generate a new Minute" option when the only version failed', () => {
    configureQuery([
      makeVersion({ id: 'v1', status: 'failed', content_source: 'ai_edit' }),
    ])
    renderEditor()

    expect(
      screen.getByText(
        'There was a problem processing your request. Try generating a new Minute.'
      )
    ).toBeInTheDocument()
    expect(
      screen.queryByRole('button', { name: 'Undo' })
    ).not.toBeInTheDocument()
  })

  it('displays the previously-selected version (not the latest) when a later AI edit fails', () => {
    configureQuery([
      makeVersion({
        id: 'v3',
        status: 'failed',
        content_source: 'ai_edit',
        html_content: '<p>failed content</p>',
      }),
      makeVersion({ id: 'v2', html_content: '<p>doc 2 content</p>' }),
      makeVersion({ id: 'v1', html_content: '<p>doc 1 content</p>' }),
    ])
    renderEditor()

    expect(screen.getByTestId('simple-editor')).toHaveTextContent(
      'doc 2 content'
    )
  })

  it('deletes the failed version and invalidates the versions query on undo', () => {
    vi.mocked(useMutation).mockImplementation(((opts: {
      mutationKey?: unknown[]
    }) =>
      opts?.mutationKey?.[0] === 'delete-minute-version'
        ? {
            mutate: deleteMutateMock,
            isPending: false,
          }
        : {
            mutate: mutateMock,
            isPending: false,
          }) as unknown as typeof useMutation)

    configureQuery([
      makeVersion({ id: 'v2', status: 'failed', content_source: 'ai_edit' }),
      makeVersion({ id: 'v1' }),
    ])
    renderEditor()

    fireEvent.change(
      screen.getByRole('combobox', { name: 'Version history' }),
      {
        target: { value: 'v2' },
      }
    )
    fireEvent.click(screen.getByRole('button', { name: /Undo/ }))

    expect(deleteMutateMock).toHaveBeenCalledWith({
      path: { minute_version_id: 'v2' },
    })
  })
})
