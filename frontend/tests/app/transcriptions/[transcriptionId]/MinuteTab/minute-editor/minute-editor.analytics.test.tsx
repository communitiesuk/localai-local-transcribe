import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { MinuteEditor } from '@/app/transcriptions/[transcriptionId]/MinuteTab/minute-editor/minute-editor'
import type {
  MinuteListItem,
  MinuteVersionResponse,
  TranscriptionGetResponse,
} from '@/lib/client'
import { copyHTML } from '@/lib/utils'
import convertAIMinutesToWordDoc from '@/lib/download-word-doc'

vi.mock(
  '@/app/transcriptions/[transcriptionId]/MinuteTab/components/editor/tiptap-editor',
  () => ({
    default: ({ initialContent }: { initialContent: string }) => (
      <div data-testid="simple-editor">{initialContent}</div>
    ),
  })
)

const RECORD_SUMMARY_INTERACTION_KEY = ['record-summary-interaction']

vi.mock('@/lib/client/@tanstack/react-query.gen', () => ({
  createMinuteVersionMinutesMinuteIdVersionsPostMutation: () => ({
    mutationKey: ['create-minute-version'],
  }),
  deleteMinuteVersionMinuteVersionsMinuteVersionIdDeleteMutation: () => ({
    mutationKey: ['delete-minute-version'],
  }),
  recordSummaryInteractionEventMinuteVersionsMinuteVersionIdAnalyticsEventsPostMutation:
    () => ({ mutationKey: RECORD_SUMMARY_INTERACTION_KEY }),
  listMinuteVersionsMinutesMinuteIdVersionsGetOptions: () => ({
    queryKey: ['minute-versions'],
  }),
  getGuardrailWarningMinuteVersionsMinuteVersionIdGuardrailsGetOptions: () => ({
    queryKey: ['guardrail-warning'],
  }),
  listMinuteVersionsMinutesMinuteIdVersionsGetQueryKey: () => [
    'minute-versions',
  ],
  listMinutesForTranscriptionTranscriptionTranscriptionIdMinutesGetQueryKey:
    () => ['minutes'],
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

vi.mock('@/lib/utils', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/lib/utils')>()),
  copyHTML: vi.fn(),
}))

vi.mock('@/lib/download-word-doc', () => ({ default: vi.fn() }))

const transcription = {
  id: 'transcription-1',
  dialogue_entries: [],
  title: 'Meeting',
  date_of_recording: '2024-03-15T09:30:00',
} as unknown as TranscriptionGetResponse

const minute = {
  id: 'minute-1',
  template_name: 'General summary',
  agenda: null,
} as unknown as MinuteListItem

const version = {
  id: 'minute-version-1',
  minute_id: 'minute-1',
  status: 'completed',
  created_datetime: '2024-01-01T00:00:00Z',
  html_content: '<p>Summary body</p>',
  error: null,
  ai_edit_instructions: null,
  content_source: 'initial_generation',
} as unknown as MinuteVersionResponse

/** The analytics mutation's mutate, isolated from the other two mutations in the component. */
const recordEventMock = vi.fn()

const renderEditor = () =>
  render(
    <MinuteEditor
      transcription={transcription}
      minute={minute}
      onRemoved={vi.fn()}
    />
  )

const confirmReview = (action: 'Copy' | 'Download') => {
  fireEvent.click(screen.getByRole('button', { name: `${action} document` }))
  fireEvent.click(screen.getByLabelText("I've reviewed the document"))
  fireEvent.click(screen.getByRole('button', { name: 'Confirm' }))
}

beforeEach(() => {
  vi.clearAllMocks()
  vi.mocked(copyHTML).mockResolvedValue(true)
  vi.mocked(convertAIMinutesToWordDoc).mockResolvedValue(true)
  vi.mocked(useQuery).mockReturnValue({
    data: [version],
    isLoading: false,
  } as unknown as ReturnType<typeof useQuery>)
  vi.mocked(useQueryClient).mockReturnValue({
    invalidateQueries: vi.fn(),
  } as unknown as ReturnType<typeof useQueryClient>)
  vi.mocked(useMutation).mockImplementation(
    (options) =>
      ({
        mutate:
          options?.mutationKey === RECORD_SUMMARY_INTERACTION_KEY
            ? recordEventMock
            : vi.fn(),
        reset: vi.fn(),
        isPending: false,
      }) as unknown as ReturnType<typeof useMutation>
  )
})

describe('<MinuteEditor /> summary analytics events', () => {
  it('records a button copy against the displayed version', async () => {
    renderEditor()

    confirmReview('Copy')

    await waitFor(() => {
      expect(recordEventMock).toHaveBeenCalledExactlyOnceWith({
        path: { minute_version_id: 'minute-version-1' },
        body: { event_type: 'summary_copied', copy_type: 'button' },
      })
    })
  })

  it('records a completed download with no copy type', async () => {
    renderEditor()

    confirmReview('Download')

    await waitFor(() => {
      expect(recordEventMock).toHaveBeenCalledExactlyOnceWith({
        path: { minute_version_id: 'minute-version-1' },
        body: { event_type: 'summary_downloaded' },
      })
    })
  })

  it('records nothing when the user cancels the save-file picker', async () => {
    vi.mocked(convertAIMinutesToWordDoc).mockResolvedValue(false)
    renderEditor()

    confirmReview('Download')

    await waitFor(() => {
      expect(convertAIMinutesToWordDoc).toHaveBeenCalled()
    })
    expect(recordEventMock).not.toHaveBeenCalled()
    expect(setBannerMock).not.toHaveBeenCalled()
  })

  it('records nothing when the user cancels the review modal', () => {
    renderEditor()

    fireEvent.click(screen.getByRole('button', { name: 'Copy document' }))
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))

    expect(recordEventMock).not.toHaveBeenCalled()
    expect(copyHTML).not.toHaveBeenCalled()
  })

  it('records a native copy made inside the summary', () => {
    renderEditor()

    const range = document.createRange()
    range.selectNodeContents(screen.getByTestId('simple-editor'))
    const selection = window.getSelection()!
    selection.removeAllRanges()
    selection.addRange(range)

    document.dispatchEvent(new Event('copy', { bubbles: true }))

    expect(recordEventMock).toHaveBeenCalledExactlyOnceWith({
      path: { minute_version_id: 'minute-version-1' },
      body: { event_type: 'summary_copied', copy_type: 'native' },
    })

    selection.removeAllRanges()
  })

  it('shows no banner when the analytics post fails, and still copies', async () => {
    // mutate is fire-and-forget: react-query swallows the rejection, so a failed insert must
    // leave the success banner and the copy itself untouched.
    recordEventMock.mockImplementation(() => {
      // what useMutation().mutate does on failure - no throw to the caller
    })
    renderEditor()

    confirmReview('Copy')

    await waitFor(() => {
      expect(copyHTML).toHaveBeenCalledTimes(1)
    })
    expect(setBannerMock).toHaveBeenCalledWith({
      variant: 'success',
      title: 'Success',
      message: "'General summary' copied to clipboard",
    })
  })
})
