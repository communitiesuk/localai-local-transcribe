import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { TranscriptionBackLink } from '@/app/transcriptions/[transcriptionId]/components/transcription-back-link'

let mockPathname = '/transcriptions/transcription-1'

vi.mock('next/navigation', () => ({
  usePathname: () => mockPathname,
  useRouter: () => ({ back: vi.fn() }),
}))

describe('<TranscriptionBackLink />', () => {
  // All distinct routes nested under /transcriptions/[transcriptionId]
  it.each([
    [
      'the transcription detail page (transcript/document/minute tabs)',
      '/transcriptions/transcription-1',
    ],
    [
      'a transcription id containing hyphens/uuids',
      '/transcriptions/9c6e6e4e-1b3a-4e0a-9e8a-9b9c6e6e4e1b',
    ],
  ])('renders exactly one back link on %s', (_label, pathname) => {
    mockPathname = pathname
    render(<TranscriptionBackLink />)

    const backLinks = screen.getAllByRole('link', { name: 'Back' })
    expect(backLinks).toHaveLength(1)
  })

  it('renders no back link on the delete confirmation interstitial', () => {
    mockPathname = '/transcriptions/transcription-1/delete'
    render(<TranscriptionBackLink />)

    expect(screen.queryByRole('link', { name: 'Back' })).not.toBeInTheDocument()
  })
})
