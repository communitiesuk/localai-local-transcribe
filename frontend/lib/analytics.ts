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

const UUID_SEGMENT =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i

const scrubUrl = (url: string): string | null => {
  try {
    const parsedUrl = new URL(url)
    if (!['https:', 'http:'].includes(parsedUrl.protocol)) {
      return null
    }
    const pathname = parsedUrl.pathname
      .split('/')
      .map((segment) =>
        UUID_SEGMENT.test(decodeURIComponent(segment)) ? '_id_' : segment
      )
      .join('/')
    return `${parsedUrl.origin}${pathname}`
  } catch {
    console.warn('Plausible: unable to sanitise analytics URL', { url })
    return null
  }
}

export const initAnalytics = () => {
  if (!PLAUSIBLE_DOMAIN || initialised) {
    return
  }

  init({
    domain: PLAUSIBLE_DOMAIN,
    autoCapturePageviews: true,
    captureOnLocalhost: true,
    // All events retain paths and referrers, with UUIDs and query params scrubbed
    transformRequest: (payload) => ({
      ...payload,
      u: scrubUrl(payload.u) ?? `https://${PLAUSIBLE_DOMAIN}/`,
      r: payload.r ? scrubUrl(payload.r) : null,
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
