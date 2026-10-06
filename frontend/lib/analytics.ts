import { init, track } from '@plausible-analytics/tracker'

export type AnalyticsEventName =
  | 'live_recording_started_or_upload_requested'
  | 'audio_upload_complete_from_live_recording'
  | 'audio_upload_complete_from_direct_upload'
  | 'transcript_requested_for_live_recording'
  | 'transcript_requested_for_direct_upload'
  | 'summary_requested'

const PLAUSIBLE_DOMAIN = process.env.NEXT_PUBLIC_PLAUSIBLE_DOMAIN

let initialised = false

export const initAnalytics = () => {
  if (!PLAUSIBLE_DOMAIN || initialised) {
    return
  }

  init({
    domain: PLAUSIBLE_DOMAIN,
    // Our paths carry transcription and recording identifiers, so no page is ever reported.
    autoCapturePageviews: false,
    captureOnLocalhost: true,
  })

  initialised = true
}

export const recordAnalyticsEvent = (
  name: AnalyticsEventName,
  props?: Record<string, string>
) => {
  if (!PLAUSIBLE_DOMAIN) {
    return
  }

  track(name, { url: `https://${PLAUSIBLE_DOMAIN}/`, props })
}
