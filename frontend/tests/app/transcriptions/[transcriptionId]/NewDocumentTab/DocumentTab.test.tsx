import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { DocumentTab } from '@/app/transcriptions/[transcriptionId]/NewDocumentTab/DocumentTab'
import {
  MinuteListItem,
  MinuteVersionResponse,
  TranscriptionGetResponse,
} from '@/lib/client'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

const versions: MinuteVersionResponse[] = [
  {
    status: 'completed',
    created_datetime: '2024-01-01T00:00:00Z',
    html_content: 'Generated version content',
  },
]

vi.mock('@/lib/client/@tanstack/react-query.gen', () => ({
  listMinuteVersionsMinutesMinuteIdVersionsGetOptions: () => ({
    queryKey: ['versions'],
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

const configureQueries = (overrides: { versions?: unknown } = {}) => {
  const versionsResult = overrides.versions ?? { data: versions }

  const queryKeyToResponse = (key: string) => {
    switch (key) {
      case 'versions':
        return versionsResult
    }
    return undefined
  }

  vi.mocked(useQuery).mockImplementation(((opts: { queryKey?: unknown[] }) =>
    queryKeyToResponse(
      opts?.queryKey?.[0] as string
    )) as unknown as typeof useQuery)
}

const mutateMock = vi.fn()

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

describe('<DocumentTab />', () => {
  it('renders document content', () => {
    render(
      <DocumentTab
        transcription={{ id: '1' } as TranscriptionGetResponse}
        minute={{ id: '1' } as MinuteListItem}
      />
    )

    expect(screen.getByText('Generated version content')).toBeInTheDocument()
  })
})
