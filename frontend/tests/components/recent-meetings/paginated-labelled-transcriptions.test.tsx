import { PaginatedLabelledTranscriptions } from '@/components/recent-meetings/paginated-labelled-transcriptions'
import { render, screen } from '@testing-library/react'
import { useQuery } from '@tanstack/react-query'
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('next/navigation', () => ({
  usePathname: () => '/my-recordings',
  useSearchParams: () => new URLSearchParams(),
  useRouter: () => ({ replace: vi.fn(), push: vi.fn() }),
}))

vi.mock('@/lib/client/@tanstack/react-query.gen', () => ({
  listLabelledTranscriptionsTranscriptionsLabelledGetOptions: () => ({
    queryKey: ['labelled-transcriptions'],
  }),
}))

vi.mock('@tanstack/react-query', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@tanstack/react-query')>()
  return { ...actual, useQuery: vi.fn() }
})

const longValue = 'A'.repeat(200)

const transcription = {
  id: 'transcription-1',
  client_name: longValue,
  case_id: longValue,
  title: longValue,
  client_date_of_birth: '1990-01-01',
  date_of_recording: '2026-01-02T09:30:00Z',
  created_datetime: '2026-01-02T09:30:00Z',
  status: 'completed',
}

beforeEach(() => {
  vi.clearAllMocks()
  vi.mocked(useQuery).mockReturnValue({
    data: { items: [transcription], total_pages: 1, total_count: 1 },
    isLoading: false,
    error: null,
  } as unknown as ReturnType<typeof useQuery>)
})

describe('<PaginatedLabelledTranscriptions />', () => {
  it('puts the table in a scrollable region a keyboard user can reach', () => {
    render(<PaginatedLabelledTranscriptions />)

    const region = screen.getByRole('region', { name: 'Labelled recordings' })

    expect(region).toHaveClass('overflow-x-auto')
    expect(region).toHaveAttribute('tabindex', '0')
    expect(region).toContainElement(screen.getByRole('table'))
  })

  it('positions the scrollable region so visually hidden cell content cannot escape it', () => {
    render(<PaginatedLabelledTranscriptions />)

    expect(
      screen.getByRole('region', { name: 'Labelled recordings' })
    ).toHaveClass('relative')
  })

  it('gives the scrollable region a visible focus state', () => {
    render(<PaginatedLabelledTranscriptions />)

    expect(
      screen.getByRole('region', { name: 'Labelled recordings' })
    ).toHaveClass('focus-visible:[outline:3px_solid_var(--govuk-focus-colour)]')
  })

  it('still shows long client names, case IDs and subjects in full', () => {
    render(<PaginatedLabelledTranscriptions />)

    expect(screen.getAllByText(longValue)).toHaveLength(3)
  })
})
