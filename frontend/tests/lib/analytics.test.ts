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
    await recordAnalyticsEvent('summary_requested')

    expect(recordAnalyticsEventAnalyticsEventsPost).toHaveBeenCalledWith({
      body: { name: 'summary_requested' },
    })
  })

  it('does not throw when the request fails', async () => {
    vi.mocked(recordAnalyticsEventAnalyticsEventsPost).mockRejectedValue(
      new Error('network error')
    )

    await expect(
      recordAnalyticsEvent('live_recording_started_or_upload_requested')
    ).resolves.toBeUndefined()
  })
})
