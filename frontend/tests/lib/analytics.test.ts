import { beforeEach, describe, expect, it, vi } from 'vitest'

import { recordAnalyticsEvent } from '@/lib/analytics'
import { recordAnalyticsEventAnalyticsEventsPost } from '@/lib/client'

vi.mock('@/lib/client', () => ({
  recordAnalyticsEventAnalyticsEventsPost: vi.fn(),
}))

describe('recordAnalyticsEvent', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('sends the event name and nothing identifying', async () => {
    await recordAnalyticsEvent('live_recording_started_or_upload_requested')

    expect(recordAnalyticsEventAnalyticsEventsPost).toHaveBeenCalledWith({
      body: { name: 'live_recording_started_or_upload_requested' },
    })
  })

  it('does not throw when the request fails', async () => {
    vi.mocked(recordAnalyticsEventAnalyticsEventsPost).mockRejectedValue(
      new Error('network error')
    )

    await expect(
      recordAnalyticsEvent('audio_upload_complete_from_direct_upload')
    ).resolves.toBeUndefined()
  })
})