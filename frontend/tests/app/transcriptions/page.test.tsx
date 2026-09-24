import { beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'
import { act, render, screen, within } from '@testing-library/react'
import TranscriptionPage from '@/app/transcriptions/[transcriptionId]/page'
import userEvent from '@testing-library/user-event/dist/cjs/index.js'
import {
  QueryClient,
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query'
import type {
  MinuteListItem,
  MinuteVersionResponse,
  TranscriptionGetResponse,
} from '@/lib/client'

const transcription: TranscriptionGetResponse = {
  id: 'transcription-1',
  title: 'Test title',
  dialogue_entries: [
    { speaker: 'Alice', text: 'Original text', start_time: 0, end_time: 1 },
  ],
  status: 'completed',
  created_datetime: '2024-01-01T00:00:00Z',
  case_id: 'case-1',
  client_name: 'Test Client',
  client_date_of_birth: '1990-01-01',
}

const twoEntryTranscription: TranscriptionGetResponse = {
  ...transcription,
  dialogue_entries: [
    { speaker: 'Alice', text: 'First line', start_time: 0, end_time: 1 },
    { speaker: 'Bob', text: 'Second line', start_time: 1, end_time: 2 },
  ],
}

const minutes: MinuteListItem[] = [
  {
    id: '1',
    transcription_id: transcription.id,
    template_name: 'test template',
  } as MinuteListItem,
]

const minuteVersions: MinuteVersionResponse[] = [
  {
    id: '1',
    status: 'completed',
    html_content: 'quote one[1] unfounded quote [100]',
  } as MinuteVersionResponse,
]

vi.mock('next/navigation', () => ({
  useRouter: () => null,
  useSearchParams: () => new URLSearchParams(),
  redirect: () => null,
}))

vi.mock('posthog-js/react', () => ({
  useFeatureFlagEnabled: () => false,
}))

vi.mock('@/lib/client/@tanstack/react-query.gen', () => ({
  listMinutesForTranscriptionTranscriptionTranscriptionIdMinutesGetOptions:
    () => ({
      queryKey: ['minutes'],
    }),
  getTranscriptionTranscriptionsTranscriptionIdGetOptions: () => ({
    queryKey: ['transcription'],
  }),
  getRecordingsForTranscriptionTranscriptionsTranscriptionIdRecordingsGetOptions:
    () => ({
      queryKey: ['recordings'],
    }),
  listMinuteVersionsMinutesMinuteIdVersionsGetOptions: () => ({
    queryKey: ['minute-versions'],
  }),
  getGuardrailWarningMinuteVersionsMinuteVersionIdGuardrailsGetOptions: () => ({
    queryKey: ['guardrail-warning'],
  }),
  updateTranscriptionMetadataTranscriptionsTranscriptionIdDetailsPutMutation:
    () => ({
      mutationKey: ['update-transcription-metadata'],
    }),
  createMinuteTranscriptionTranscriptionIdMinutesPostMutation: () => ({
    mutationKey: ['create-minute'],
  }),
  createMinuteVersionMinutesMinuteIdVersionsPostMutation: () => ({
    mutationKey: ['create-minute-version'],
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

const configureQueries = () => {
  const queryKeyToResponse = (key: string) => {
    switch (key) {
      case 'transcription':
        return { data: twoEntryTranscription }
      case 'minutes':
        return { data: minutes }
      case 'recordings':
        return { data: [] }
      case 'minute-versions':
        return { data: minuteVersions }
      case 'guardrail-warning':
        return { data: { message: null } }
    }
    return undefined
  }

  vi.mocked(useQuery).mockImplementation(((opts: { queryKey?: unknown[] }) =>
    queryKeyToResponse(
      opts?.queryKey?.[0] as string
    )) as unknown as typeof useQuery)
}

describe('<TranscriptionPage /> View quote', () => {
  beforeAll(() => {
    // We stub this method because tiptap expects to be running in a real DOM
    // and so this method to be present. The tests, however, run with jsDOM
    // where this function doesn't exist.
    document.elementFromPoint = () => null
  })

  beforeEach(() => {
    vi.clearAllMocks()
    configureQueries()
    vi.mocked(useMutation).mockReturnValue({
      mutate: () => {},
      isPending: false,
    } as unknown as ReturnType<typeof useMutation>)
    Element.prototype.scrollIntoView = () => {}

    vi.mocked(useQueryClient).mockReturnValue({
      setQueryData: vi.fn(),
      invalidateQueries: vi.fn(),
    } as unknown as QueryClient)
  })

  it('should change tab to transcription when quote is clicked', async () => {
    await act(async () =>
      render(
        <TranscriptionPage params={Promise.resolve({ transcriptionId: '1' })} />
      )
    )

    const minuteTabLink = screen.getByRole('tab', { name: 'test template' })
    expect(minuteTabLink).toBeInTheDocument()

    await userEvent.click(minuteTabLink)

    const templateTab = screen.getByLabelText('test template')

    expect(templateTab).toBeInTheDocument()
    const citationLink = within(templateTab).getByText('[1]')
    expect(citationLink).toBeInTheDocument()

    await userEvent.click(citationLink)

    const transcriptTabLink = screen.getByRole('tab', { name: 'Transcript' })

    expect(transcriptTabLink).toHaveAttribute('aria-selected', 'true')
  })

  it("should not change tab, and show error when quote doesn't link to a line in the transcript", async () => {
    await act(async () =>
      render(
        <TranscriptionPage params={Promise.resolve({ transcriptionId: '1' })} />
      )
    )

    const minuteTabLink = screen.getByRole('tab', { name: 'test template' })
    expect(minuteTabLink).toBeInTheDocument()

    await userEvent.click(minuteTabLink)

    const templateTab = screen.getByLabelText('test template')

    expect(templateTab).toBeInTheDocument()
    const citationLink = within(templateTab).getByText('[100]')
    expect(citationLink).toBeInTheDocument()

    await userEvent.click(citationLink)

    const transcriptTabLink = screen.getByRole('tab', { name: 'Transcript' })

    expect(transcriptTabLink).toHaveAttribute('aria-selected', 'false')

    expect(
      screen.getByText(
        'Quote [100] is not attributed to anything in the transcript'
      )
    ).toBeInTheDocument()
  })
})

describe('<TranscriptionPage /> Edit transcript', () => {
  beforeAll(() => {
    // We stub this method because tiptap expects to be running in a real DOM
    // and so this method to be present. The tests, however, run with jsDOM
    // where this function doesn't exist.
    document.elementFromPoint = () => null

    // same for innerText
    Object.defineProperty(HTMLElement.prototype, 'innerText', {
      get() {
        return this.textContent
      },
    })
  })

  beforeEach(() => {
    vi.clearAllMocks()
    configureQueries()
    vi.mocked(useMutation).mockReturnValue({
      mutate: () => {},
      isPending: false,
    } as unknown as ReturnType<typeof useMutation>)
    Element.prototype.scrollIntoView = () => {}

    vi.mocked(useQueryClient).mockReturnValue({
      setQueryData: vi.fn(),
      invalidateQueries: vi.fn(),
    } as unknown as QueryClient)
  })

  it('should change tab to document tab on click when no edit in progress', async () => {
    await act(async () =>
      render(
        <TranscriptionPage params={Promise.resolve({ transcriptionId: '1' })} />
      )
    )

    const transcriptTabLink = screen.getByRole('tab', { name: 'Transcript' })
    expect(transcriptTabLink).toBeInTheDocument()

    await userEvent.click(transcriptTabLink)
    expect(transcriptTabLink).toHaveAttribute('aria-selected', 'true')

    const documentTabLink = screen.getByRole('tab', { name: 'test template' })
    expect(documentTabLink).toBeInTheDocument()

    await userEvent.click(documentTabLink)
    expect(documentTabLink).toHaveAttribute('aria-selected', 'true')
  })

  it('should show an are you sure modal on click navigation to document tab when transcript edit in progress', async () => {
    await act(async () =>
      render(
        <TranscriptionPage params={Promise.resolve({ transcriptionId: '1' })} />
      )
    )

    const transcriptTabLink = screen.getByRole('tab', { name: 'Transcript' })
    expect(transcriptTabLink).toBeInTheDocument()

    await userEvent.click(transcriptTabLink)
    expect(transcriptTabLink).toHaveAttribute('aria-selected', 'true')

    const editTranscriptButton = screen.getByRole('button', {
      name: 'Edit transcript',
    })
    await userEvent.click(editTranscriptButton)

    const transcriptLine = screen.getByText('First line')
    await userEvent.click(transcriptLine)

    expect(transcriptLine).toHaveAttribute('contenteditable', 'true')

    await userEvent.type(transcriptLine, ' edited')

    expect(screen.getByText('First line edited')).toBeInTheDocument()

    const documentTabLink = screen.getByRole('tab', { name: 'test template' })
    expect(documentTabLink).toBeInTheDocument()

    await userEvent.click(documentTabLink)
    expect(documentTabLink).toHaveAttribute('aria-selected', 'false')

    const areYouSureModal = screen.getByRole('dialog')
    expect(areYouSureModal).toBeInTheDocument()

    expect(
      within(areYouSureModal).getByText('Discard changes to transcript?')
    ).toBeInTheDocument()
    expect(
      within(areYouSureModal).getByText(
        'If you continue, your unsaved changes to the current line edit will be lost.'
      )
    ).toBeInTheDocument()

    expect(
      within(areYouSureModal).getByRole('button', { name: 'Discard changes' })
    ).toBeInTheDocument()
    expect(
      within(areYouSureModal).getByRole('button', { name: 'Cancel' })
    ).toBeInTheDocument()
    expect(
      within(areYouSureModal).getByRole('button', { name: 'Close' })
    ).toBeInTheDocument()
  })

  it('clicking close in the are you sure modal should close the modal and preserve edits', async () => {
    await act(async () =>
      render(
        <TranscriptionPage params={Promise.resolve({ transcriptionId: '1' })} />
      )
    )

    const transcriptTabLink = screen.getByRole('tab', { name: 'Transcript' })
    expect(transcriptTabLink).toBeInTheDocument()

    await userEvent.click(transcriptTabLink)
    expect(transcriptTabLink).toHaveAttribute('aria-selected', 'true')

    const editTranscriptButton = screen.getByRole('button', {
      name: 'Edit transcript',
    })
    await userEvent.click(editTranscriptButton)

    const transcriptLine = screen.getByText('First line')
    await userEvent.click(transcriptLine)

    expect(transcriptLine).toHaveAttribute('contenteditable', 'true')

    await userEvent.type(transcriptLine, ' edited')

    expect(screen.getByText('First line edited')).toBeInTheDocument()

    const documentTabLink = screen.getByRole('tab', { name: 'test template' })
    expect(documentTabLink).toBeInTheDocument()

    await userEvent.click(documentTabLink)
    expect(documentTabLink).toHaveAttribute('aria-selected', 'false')

    const areYouSureModal = screen.getByRole('dialog')
    expect(areYouSureModal).toBeInTheDocument()

    const closeModalButton = within(areYouSureModal).getByRole('button', {
      name: 'Close',
    })
    expect(closeModalButton).toBeInTheDocument()

    await userEvent.click(closeModalButton)

    expect(areYouSureModal).not.toBeInTheDocument()

    expect(screen.getByText('First line edited')).toBeInTheDocument()
  })

  it('clicking cancel in the are you sure modal should close the modal and preserve edits', async () => {
    await act(async () =>
      render(
        <TranscriptionPage params={Promise.resolve({ transcriptionId: '1' })} />
      )
    )

    const transcriptTabLink = screen.getByRole('tab', { name: 'Transcript' })
    expect(transcriptTabLink).toBeInTheDocument()

    await userEvent.click(transcriptTabLink)
    expect(transcriptTabLink).toHaveAttribute('aria-selected', 'true')

    const editTranscriptButton = screen.getByRole('button', {
      name: 'Edit transcript',
    })
    await userEvent.click(editTranscriptButton)

    const transcriptLine = screen.getByText('First line')
    await userEvent.click(transcriptLine)

    expect(transcriptLine).toHaveAttribute('contenteditable', 'true')

    await userEvent.type(transcriptLine, ' edited')

    expect(screen.getByText('First line edited')).toBeInTheDocument()

    const documentTabLink = screen.getByRole('tab', { name: 'test template' })
    expect(documentTabLink).toBeInTheDocument()

    await userEvent.click(documentTabLink)
    expect(documentTabLink).toHaveAttribute('aria-selected', 'false')

    const areYouSureModal = screen.getByRole('dialog')
    expect(areYouSureModal).toBeInTheDocument()

    const cancelModalButton = within(areYouSureModal).getByRole('button', {
      name: 'Cancel',
    })
    expect(cancelModalButton).toBeInTheDocument()

    await userEvent.click(cancelModalButton)

    expect(areYouSureModal).not.toBeInTheDocument()

    expect(screen.getByText('First line edited')).toBeInTheDocument()
  })

  it('clicking discard changes in the are you sure modal should close the modal, discards edits, and continues navigation', async () => {
    await act(async () =>
      render(
        <TranscriptionPage params={Promise.resolve({ transcriptionId: '1' })} />
      )
    )

    const transcriptTabLink = screen.getByRole('tab', { name: 'Transcript' })
    expect(transcriptTabLink).toBeInTheDocument()

    await userEvent.click(transcriptTabLink)
    expect(transcriptTabLink).toHaveAttribute('aria-selected', 'true')

    const editTranscriptButton = screen.getByRole('button', {
      name: 'Edit transcript',
    })
    await userEvent.click(editTranscriptButton)

    const transcriptLine = screen.getByText('First line')
    await userEvent.click(transcriptLine)

    expect(transcriptLine).toHaveAttribute('contenteditable', 'true')

    await userEvent.type(transcriptLine, ' edited')

    expect(screen.getByText('First line edited')).toBeInTheDocument()

    const documentTabLink = screen.getByRole('tab', { name: 'test template' })
    expect(documentTabLink).toBeInTheDocument()

    await userEvent.click(documentTabLink)
    expect(documentTabLink).toHaveAttribute('aria-selected', 'false')

    const areYouSureModal = screen.getByRole('dialog')
    expect(areYouSureModal).toBeInTheDocument()

    const discardChangesButton = within(areYouSureModal).getByRole('button', {
      name: 'Discard changes',
    })
    expect(discardChangesButton).toBeInTheDocument()

    await userEvent.click(discardChangesButton)

    expect(areYouSureModal).not.toBeInTheDocument()

    expect(screen.queryByText('First line edited')).not.toBeInTheDocument()
    expect(documentTabLink).toHaveAttribute('aria-selected', 'true')
    expect(screen.queryByText('There is a problem')).not.toBeInTheDocument()
    expect(
      screen.queryByText(
        'You must save or cancel your line edit to finish editing'
      )
    ).not.toBeInTheDocument()
  })

  it('modal is not shown and edit automatically finished if no line edit in progress on tab change', async () => {
    await act(async () =>
      render(
        <TranscriptionPage params={Promise.resolve({ transcriptionId: '1' })} />
      )
    )

    const transcriptTabLink = screen.getByRole('tab', { name: 'Transcript' })
    expect(transcriptTabLink).toBeInTheDocument()

    await userEvent.click(transcriptTabLink)
    expect(transcriptTabLink).toHaveAttribute('aria-selected', 'true')

    const editTranscriptButton = screen.getByRole('button', {
      name: 'Edit transcript',
    })
    await userEvent.click(editTranscriptButton)

    const transcriptLine = screen.getByText('First line')
    await userEvent.click(transcriptLine)

    expect(transcriptLine).toHaveAttribute('contenteditable', 'true')

    const finishEditingButton = screen.getByRole('button', {
      name: 'Finish editing',
    })
    expect(finishEditingButton).toBeInTheDocument()
    expect(finishEditingButton).toBeEnabled()

    const documentTabLink = screen.getByRole('tab', { name: 'test template' })
    expect(documentTabLink).toBeInTheDocument()

    await userEvent.click(documentTabLink)

    const areYouSureModal = screen.queryByRole('dialog')
    expect(areYouSureModal).not.toBeInTheDocument()

    expect(documentTabLink).toHaveAttribute('aria-selected', 'true')
    expect(finishEditingButton).not.toBeInTheDocument()
  })
})
