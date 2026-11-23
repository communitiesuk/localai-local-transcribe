/* eslint-disable @typescript-eslint/no-explicit-any */
import { act, render, screen } from '@testing-library/react'
import { useQuery } from '@tanstack/react-query'
import { useRouter, useSearchParams } from 'next/navigation'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import AddRecordingMetadataPage from '@/app/new/metadata/[transcriptionId]/page'

vi.mock('@/lib/client/@tanstack/react-query.gen', () => ({
  getTranscriptionTranscriptionsTranscriptionIdGetOptions: vi.fn(() => ({
    queryKey: ['transcription'],
  })),
}))

vi.mock('next/navigation', () => ({
  useRouter: vi.fn(),
  useSearchParams: vi.fn(),
  usePathname: vi.fn(() => '/new/metadata/transcription-1'),
  redirect: vi.fn(),
}))

vi.mock('@tanstack/react-query', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@tanstack/react-query')>()
  return { ...actual, useQuery: vi.fn() }
})

vi.mock('@/app/transcriptions/[transcriptionId]/RecordingDetails', () => ({
  RecordingDetails: () => <div>Recording details</div>,
}))

const transcription = {
  id: 'transcription-1',
  status: 'in_progress',
  created_datetime: '2026-11-19T09:00:00Z',
}

const limitWarning = /This recording reached 2 hours and has stopped\./

describe('<AddRecordingMetadataPage />', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(useRouter).mockReturnValue({ push: vi.fn() } as any)
    vi.mocked(useQuery).mockReturnValue({
      data: transcription,
      isLoading: false,
    } as any)
  })

  const renderPage = async (search: string) => {
    vi.mocked(useSearchParams).mockReturnValue(
      new URLSearchParams(search) as any
    )

    await act(async () =>
      render(
        <AddRecordingMetadataPage
          params={Promise.resolve({ transcriptionId: 'transcription-1' })}
        />
      )
    )
  }

  it('keeps telling the user the recording stopped at the limit', async () => {
    await renderPage('stoppedAtLimit=true')

    expect(screen.getByText(limitWarning)).toBeInTheDocument()
  })

  it('says nothing about the limit when the recording was stopped by the user', async () => {
    await renderPage('')

    expect(screen.queryByText(limitWarning)).not.toBeInTheDocument()
  })
})
