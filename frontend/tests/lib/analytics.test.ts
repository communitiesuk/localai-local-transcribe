import { beforeEach, describe, expect, it, vi } from 'vitest'

import { init, track } from '@plausible-analytics/tracker'

vi.mock('@plausible-analytics/tracker', () => ({
  init: vi.fn(),
  track: vi.fn(),
}))

const loadAnalytics = async () => {
  vi.resetModules()
  return import('@/lib/analytics')
}

describe('analytics', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.stubEnv('NEXT_PUBLIC_PLAUSIBLE_DOMAIN', 'transcribe.test')
  })

  it('sends the event to Plausible from the browser', async () => {
    const { recordAnalyticsEvent } = await loadAnalytics()

    recordAnalyticsEvent('summary_requested')

    expect(track).toHaveBeenCalledWith('summary_requested', {
      props: undefined,
    })
  })

  it('sends neither our page nor our referrer, so no identifiers reach Plausible', async () => {
    const { initAnalytics } = await loadAnalytics()

    initAnalytics()
    const { transformRequest } = vi.mocked(init).mock.calls[0][0]

    expect(
      transformRequest?.({
        n: 'summary_requested',
        u: 'https://transcribe.test/transcriptions/9f1b-uuid',
        d: 'transcribe.test',
        r: 'https://transcribe.test/recordings/3c7a-uuid',
      })
    ).toEqual({
      n: 'summary_requested',
      u: 'https://transcribe.test/',
      d: 'transcribe.test',
      r: null,
    })
  })

  it('sends the organisation as a custom property', async () => {
    const { recordAnalyticsEvent } = await loadAnalytics()

    recordAnalyticsEvent('audio_upload_complete_from_direct_upload', {
      organisation_id: 'organisation-1',
    })

    expect(track).toHaveBeenCalledWith(
      'audio_upload_complete_from_direct_upload',
      expect.objectContaining({ props: { organisation_id: 'organisation-1' } })
    )
  })

  it('initialises once, with page views off', async () => {
    const { initAnalytics } = await loadAnalytics()

    initAnalytics()
    initAnalytics()

    expect(init).toHaveBeenCalledTimes(1)
    expect(init).toHaveBeenCalledWith(
      expect.objectContaining({
        domain: 'transcribe.test',
        autoCapturePageviews: false,
        captureOnLocalhost: true,
      })
    )
  })

  it('does nothing when no site is configured', async () => {
    vi.stubEnv('NEXT_PUBLIC_PLAUSIBLE_DOMAIN', '')
    const { initAnalytics, recordAnalyticsEvent } = await loadAnalytics()

    initAnalytics()
    recordAnalyticsEvent('summary_requested')

    expect(init).not.toHaveBeenCalled()
    expect(track).not.toHaveBeenCalled()
  })
})
