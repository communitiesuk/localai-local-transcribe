import { init, track } from '@plausible-analytics/tracker'

export type AnalyticsEventName =
  | 'live_recording_started'
  | 'audio_upload_requested'
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
    autoCapturePageviews: false,
    captureOnLocalhost: true,
    // Our paths and referrers carry transcription and recording identifiers, so neither is ever sent.
    transformRequest: (payload) => ({
      ...payload,
      u: `https://${PLAUSIBLE_DOMAIN}/`,
      r: null,
    }),
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

  track(name, { props })
}
