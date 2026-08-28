import { render, screen, fireEvent } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { NewDocumentTab } from '@/app/transcriptions/[transcriptionId]/NewDocumentTab/NewDocumentTab'
import type { TranscriptionGetResponse } from '@/lib/client'

vi.mock('posthog-js', () => ({ default: { capture: vi.fn() } }))

const setBannerMock = vi.hoisted(() => vi.fn())
vi.mock('@/stores/use-banner-store', () => ({
  useBannerStore: (selector: (s: { setBanner: unknown }) => unknown) =>
    selector({ setBanner: setBannerMock }),
}))

vi.mock('@/lib/client/@tanstack/react-query.gen', () => ({
  getUserTemplatesUserTemplatesGetOptions: () => ({ queryKey: ['templates'] }),
  listMinuteVersionsMinutesMinuteIdVersionsGetOptions: () => ({
    queryKey: ['versions'],
  }),
  listMinutesForTranscriptionTranscriptionTranscriptionIdMinutesGetQueryKey:
    () => ['minutes'],
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

const transcription = { id: 'transcription-1' } as TranscriptionGetResponse

const templates = [
  { id: 't1', name: 'General summary', description: 'Standard summary' },
  { id: 't2', name: 'Triage assessment', description: 'Standardised form' },
]

const configureQueries = (
  overrides: { templates?: unknown; versions?: unknown } = {}
) => {
  const templatesResult = overrides.templates ?? {
    data: templates,
    isLoading: false,
    isError: false,
    refetch: vi.fn(),
  }
  const versionsResult = overrides.versions ?? { data: [] }
  vi.mocked(useQuery).mockImplementation(((opts: { queryKey?: unknown[] }) =>
    opts?.queryKey?.[0] === 'versions'
      ? versionsResult
      : templatesResult) as unknown as typeof useQuery)
}

const mutateMock = vi.fn()

const renderTab = (
  props: Partial<React.ComponentProps<typeof NewDocumentTab>> = {}
) =>
  render(
    <NewDocumentTab
      transcription={transcription}
      onCancel={vi.fn()}
      onCreated={vi.fn()}
      {...props}
    />
  )

const selectAndCreate = () => {
  fireEvent.click(screen.getByRole('radio', { name: /General summary/ }))
  fireEvent.click(screen.getByRole('button', { name: 'Create' }))
}

beforeEach(() => {
  vi.clearAllMocks()
  configureQueries()
  vi.mocked(useMutation).mockReturnValue({
    mutate: mutateMock,
    isPending: false,
  } as unknown as ReturnType<typeof useMutation>)
  vi.mocked(useQueryClient).mockReturnValue({
    invalidateQueries: vi.fn(),
  } as unknown as ReturnType<typeof useQueryClient>)
})

describe('<NewDocumentTab />', () => {
  it('renders the template chooser with heading, help text and the templates', () => {
    renderTab()
    expect(
      screen.getByRole('heading', { name: 'Choose a document template' })
    ).toBeInTheDocument()
    expect(
      screen.getByText('Choose a template style for your conversation')
    ).toBeInTheDocument()
    expect(
      screen.getByRole('radio', { name: /General summary/ })
    ).toBeInTheDocument()
    expect(
      screen.getByRole('radio', { name: /Triage assessment/ })
    ).toBeInTheDocument()
  })

  it('disables Create until a template is selected', () => {
    renderTab()
    expect(screen.getByRole('button', { name: 'Create' })).toBeDisabled()
    fireEvent.click(screen.getByRole('radio', { name: /General summary/ }))
    expect(screen.getByRole('button', { name: 'Create' })).toBeEnabled()
  })

  it('calls onCancel when Cancel is clicked', () => {
    const onCancel = vi.fn()
    renderTab({ onCancel })
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))
    expect(onCancel).toHaveBeenCalledOnce()
  })

  it('shows an error with a retry action when templates fail to load', () => {
    const refetch = vi.fn()
    configureQueries({
      templates: { data: undefined, isLoading: false, isError: true, refetch },
    })
    renderTab()
    expect(
      screen.getByText('Something went wrong fetching your templates.')
    ).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Try again' }))
    expect(refetch).toHaveBeenCalledOnce()
  })

  it('does not render the chooser while templates are loading', () => {
    configureQueries({
      templates: {
        data: undefined,
        isLoading: true,
        isError: false,
        refetch: vi.fn(),
      },
    })
    renderTab()
    expect(
      screen.queryByRole('heading', { name: 'Choose a document template' })
    ).not.toBeInTheDocument()
  })

  it('creates the minute and shows the creating spinner while generating', () => {
    mutateMock.mockImplementation((_vars, opts) =>
      opts?.onSuccess?.({ minute_id: 'm1' }, _vars, undefined)
    )
    configureQueries({ versions: { data: [{ status: 'in_progress' }] } })
    renderTab()

    selectAndCreate()

    expect(mutateMock).toHaveBeenCalledWith(
      {
        path: { transcription_id: 'transcription-1' },
        body: { template_name: 'General summary', template_id: 't1' },
      },
      expect.anything()
    )
    expect(screen.getByText('Creating ‘General summary’…')).toBeInTheDocument()
  })

  it('renames the tab and shows the document view when generation completes', () => {
    mutateMock.mockImplementation((_vars, opts) =>
      opts?.onSuccess?.({ minute_id: 'm1' }, _vars, undefined)
    )
    configureQueries({ versions: { data: [{ status: 'completed' }] } })
    const onCreated = vi.fn()
    renderTab({ onCreated })

    selectAndCreate()

    expect(onCreated).toHaveBeenCalledWith('General summary')
    expect(
      screen.getByText('Your ‘General summary’ document is ready.')
    ).toBeInTheDocument()
  })

  it('shows an error banner and returns to the picker when generation fails', () => {
    mutateMock.mockImplementation((_vars, opts) =>
      opts?.onSuccess?.({ minute_id: 'm1' }, _vars, undefined)
    )
    configureQueries({ versions: { data: [{ status: 'failed' }] } })
    renderTab()

    selectAndCreate()

    expect(setBannerMock).toHaveBeenCalledWith(
      expect.objectContaining({ variant: 'important' })
    )
    expect(
      screen.getByRole('heading', { name: 'Choose a document template' })
    ).toBeInTheDocument()
  })

  it('shows an error banner when the create request fails', () => {
    mutateMock.mockImplementation((_vars, opts) =>
      opts?.onError?.(new Error('boom'), _vars, undefined)
    )
    renderTab()

    selectAndCreate()

    expect(setBannerMock).toHaveBeenCalledWith(
      expect.objectContaining({ variant: 'important' })
    )
    expect(
      screen.getByRole('heading', { name: 'Choose a document template' })
    ).toBeInTheDocument()
  })
})
