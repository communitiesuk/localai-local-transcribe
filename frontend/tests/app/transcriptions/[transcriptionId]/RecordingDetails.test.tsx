import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { RecordingDetails } from '@/app/transcriptions/[transcriptionId]/RecordingDetails'
import type { TranscriptionGetResponse } from '@/lib/client'

vi.mock('@/lib/client/@tanstack/react-query.gen', () => ({
  getTranscriptionTranscriptionsTranscriptionIdGetQueryKey: () => [
    'transcription',
  ],
  updateTranscriptionMetadataTranscriptionsTranscriptionIdDetailsPutMutation:
    () => ({ mutationKey: ['update-details'] }),
}))

vi.mock('@tanstack/react-query', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@tanstack/react-query')>()
  return {
    ...actual,
    useMutation: vi.fn(),
    useQueryClient: vi.fn(),
  }
})

vi.mock('next/navigation', () => ({
  useRouter: vi.fn(),
}))

const baseTranscription = {
  id: 'transcription-1',
  created_datetime: '2024-01-01T00:00:00',
  date_of_recording: null,
  is_upload: false,
  client_name: null,
  case_id: null,
  title: null,
  client_date_of_birth: null,
} as unknown as TranscriptionGetResponse

const renderRecordingDetails = (
  overrides: Partial<TranscriptionGetResponse> = {}
) =>
  render(
    <RecordingDetails
      dateTimeLabel="1 January 2024 at 00:00"
      transcription={{ ...baseTranscription, ...overrides }}
      onErrorListChange={vi.fn()}
    />
  )

describe('RecordingDetails', () => {
  beforeEach(() => {
    vi.mocked(useMutation).mockReturnValue({
      mutate: vi.fn(),
    } as unknown as ReturnType<typeof useMutation>)
    vi.mocked(useQueryClient).mockReturnValue({
      invalidateQueries: vi.fn(),
    } as unknown as ReturnType<typeof useQueryClient>)
    vi.mocked(useRouter).mockReturnValue({
      push: vi.fn(),
    } as unknown as ReturnType<typeof useRouter>)
  })

  it('shows an editable date and time recorded, pre-populated from date_of_recording, for uploaded files', () => {
    const { container } = renderRecordingDetails({
      is_upload: true,
      date_of_recording: '2024-03-15T09:30:00',
    })

    expect(container.querySelector('#date-recorded-day')).toHaveValue('15')
    expect(container.querySelector('#date-recorded-month')).toHaveValue('3')
    expect(container.querySelector('#date-recorded-year')).toHaveValue('2024')
    expect(screen.getByLabelText('Time recorded')).toHaveValue('09:30')
  })

  it('falls back to pre-populating the editable date from created_datetime when no date_of_recording is set', () => {
    const { container } = renderRecordingDetails({
      is_upload: true,
      date_of_recording: null,
      created_datetime: '2024-06-02T14:45:00',
    })

    expect(container.querySelector('#date-recorded-day')).toHaveValue('2')
    expect(container.querySelector('#date-recorded-month')).toHaveValue('6')
    expect(container.querySelector('#date-recorded-year')).toHaveValue('2024')
    expect(screen.getByLabelText('Time recorded')).toHaveValue('14:45')
  })

  it('shows a read-only date recorded label instead of editable fields for live (non-upload) recordings', () => {
    const { container } = renderRecordingDetails({ is_upload: false })

    expect(
      container.querySelector('#date-recorded-day')
    ).not.toBeInTheDocument()
    expect(screen.queryByLabelText('Time recorded')).not.toBeInTheDocument()
    expect(screen.getByText('1 January 2024 at 00:00')).toBeInTheDocument()
  })
})
