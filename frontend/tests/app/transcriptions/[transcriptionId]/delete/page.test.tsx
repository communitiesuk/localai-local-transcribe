/* eslint-disable @typescript-eslint/no-explicit-any */
import { act, render, screen } from '@testing-library/react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import DeleteTranscriptionPage from '@/app/transcriptions/[transcriptionId]/delete/page'
import TranscriptionLayout from '@/app/transcriptions/[transcriptionId]/layout'
import { useBannerStore } from '@/stores/use-banner-store'

vi.mock('@/lib/client/@tanstack/react-query.gen', () => ({
  deleteTranscriptionTranscriptionsTranscriptionIdDeleteMutation: vi.fn(
    () => ({})
  ),
  listLabelledTranscriptionsTranscriptionsLabelledGetQueryKey: vi.fn(() => [
    'labelled',
  ]),
  listUnlabelledTranscriptionsTranscriptionsUnlabelledGetQueryKey: vi.fn(() => [
    'unlabelled',
  ]),
}))

vi.mock('next/navigation', () => ({
  useRouter: vi.fn(),
  usePathname: () => '/transcriptions/transcription-1/delete',
}))

vi.mock('@tanstack/react-query', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@tanstack/react-query')>()
  return { ...actual, useMutation: vi.fn(), useQueryClient: vi.fn() }
})

vi.mock('@/stores/use-banner-store', () => ({
  useBannerStore: vi.fn(),
}))

const mutationState = { isPending: false, isSuccess: false }

describe('<DeleteTranscriptionPage />', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mutationState.isPending = false
    mutationState.isSuccess = false

    vi.mocked(useRouter).mockReturnValue({
      push: vi.fn(),
      back: vi.fn(),
    } as any)
    vi.mocked(useQueryClient).mockReturnValue({
      invalidateQueries: vi.fn(),
    } as any)
    vi.mocked(useMutation).mockImplementation(
      () => ({ mutate: vi.fn(), ...mutationState }) as any
    )
    vi.mocked(useBannerStore).mockImplementation((selector: any) =>
      selector({ setBanner: vi.fn() })
    )
  })

  const renderPage = async () =>
    act(async () =>
      render(
        <TranscriptionLayout>
          <DeleteTranscriptionPage
            params={Promise.resolve({ transcriptionId: 'transcription-1' })}
          />
        </TranscriptionLayout>
      )
    )

  it('asks for confirmation before the recording is deleted', async () => {
    await renderPage()

    expect(
      screen.getByRole('heading', {
        name: 'Are you sure you want to delete this recording?',
      })
    ).toBeInTheDocument()
    expect(screen.queryByText('Deleting recording…')).not.toBeInTheDocument()
  })

  it('does not render a back link on the delete confirmation interstitial', async () => {
    await renderPage()

    expect(screen.queryByRole('link', { name: 'Back' })).not.toBeInTheDocument()
  })

  it('keeps the pending page up after the recording has been deleted', async () => {
    mutationState.isSuccess = true
    await renderPage()

    expect(screen.getByText('Deleting recording…')).toBeInTheDocument()
    expect(screen.queryByRole('heading')).not.toBeInTheDocument()
    expect(
      screen.queryByRole('link', { name: 'Cancel' })
    ).not.toBeInTheDocument()
  })
})
