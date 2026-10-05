import { recordAnalyticsEventAnalyticsEventsPost } from '@/lib/client'
import type { AnalyticsEventName } from '@/lib/client'

export const recordAnalyticsEvent = async (name: AnalyticsEventName) => {
  try {
    await recordAnalyticsEventAnalyticsEventsPost({ body: { name } })
  } catch {
    // Analytics must never interrupt what the user is doing.
  }
}
