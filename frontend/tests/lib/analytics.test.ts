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

  it.each(['pageview', 'summary_requested', 'audio_upload_requested'])(
    'scrubs the page and referrer for %s',
    async (name) => {
      const { initAnalytics } = await loadAnalytics()

      initAnalytics()
      const { transformRequest } = vi.mocked(init).mock.calls[0][0]

      expect(
        transformRequest?.({
          n: name,
          u: 'https://transcribe.test/transcriptions/12345678-1234-1234-1234-123456789abc?email=private#private',
          d: 'transcribe.test',
          r: 'https://referrer.test/recordings/12345678-1234-1234-1234-123456789abc?token=private#private',
        })
      ).toEqual({
        n: name,
        u: 'https://transcribe.test/transcriptions/_id_',
        d: 'transcribe.test',
        r: 'https://referrer.test/recordings/_id_',
      })
    }
  )

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

  it.each([
    ['/support', '/support'],
    ['/new/record/in-person', '/new/record/in-person'],
    ['/new/record/online', '/new/record/online'],
    ['/templates/new/confirm', '/templates/new/confirm'],
    [
      '/transcriptions/12345678-1234-1234-1234-123456789abc',
      '/transcriptions/_id_',
    ],
    ['/recordings/12345678-1234-1234-1234-123456789abc', '/recordings/_id_'],
    [
      '/templates/12345678-1234-1234-1234-123456789abc/delete',
      '/templates/_id_/delete',
    ],
    [
      '/user-management/users/12345678-1234-1234-1234-123456789ABC/delete',
      '/user-management/users/_id_/delete',
    ],
    [
      '/user-management/organisations/12345678-1234-1234-1234-123456789abc/domains',
      '/user-management/organisations/_id_/domains',
    ],
    [
      '/new/metadata/12345678-1234-1234-1234-123456789abc',
      '/new/metadata/_id_',
    ],
    [
      '/templates/default/default-meeting-notes/duplicate',
      '/templates/default/default-meeting-notes/duplicate',
    ],
    [
      '/transcriptions/%31%32%33%34%35%36%37%38-1234-1234-1234-123456789abc',
      '/transcriptions/_id_',
    ],
    ['/support?email=person@example.com#private', '/support'],
    [
      '/user-management?organisationId=12345678-1234-1234-1234-123456789abc',
      '/user-management',
    ],
    [
      '/transcriptions/12345678-1234-1234-1234-123456789abc/12345678-1234-1234-1234-123456789abc',
      '/transcriptions/_id_/_id_',
    ],
  ])('sanitises pageviews for %s', async (path, expectedPath) => {
    const { initAnalytics } = await loadAnalytics()
    initAnalytics()
    const { transformRequest } = vi.mocked(init).mock.calls[0][0]

    expect(
      transformRequest?.({
        n: 'pageview',
        u: `https://actual-host.test${path}`,
        d: 'transcribe.test',
        r: null,
      })
    ).toEqual({
      n: 'pageview',
      u: `https://actual-host.test${expectedPath}`,
      d: 'transcribe.test',
      r: null,
    })
  })

  it.each([
    [undefined, null],
    [null, null],
    ['', null],
    ['not a URL', null],
    ['javascript:alert(1)', null],
    [
      'https://referrer.test/support?email=private#private',
      'https://referrer.test/support',
    ],
    [
      'https://referrer.test/templates/default/default-meeting-notes/duplicate',
      'https://referrer.test/templates/default/default-meeting-notes/duplicate',
    ],
    ['https://username:password@referrer.test/', 'https://referrer.test/'],
    [
      'https://referrer.test/transcriptions/%31%32%33%34%35%36%37%38-1234-1234-1234-123456789abc',
      'https://referrer.test/transcriptions/_id_',
    ],
  ])('scrubs or omits referrer %s', async (referrer, expected) => {
    const { initAnalytics } = await loadAnalytics()
    initAnalytics()
    const { transformRequest } = vi.mocked(init).mock.calls[0][0]
    expect(
      transformRequest?.({
        n: 'summary_requested',
        u: 'https://transcribe.test/',
        d: 'transcribe.test',
        r: referrer,
      })?.r
    ).toBe(expected)
  })

  it.each([
    'not a URL',
    'https://transcribe.test/support/%invalid',
    'javascript:alert(1)',
  ])('falls back to the root for invalid event URL %s', async (url) => {
    const { initAnalytics } = await loadAnalytics()
    initAnalytics()
    const { transformRequest } = vi.mocked(init).mock.calls[0][0]
    expect(
      transformRequest?.({
        n: 'pageview',
        u: url,
        d: 'transcribe.test',
      })?.u
    ).toBe('https://transcribe.test/')
  })

  it('initialises once, with automatic page views on', async () => {
    const { initAnalytics } = await loadAnalytics()

    initAnalytics()
    initAnalytics()

    expect(init).toHaveBeenCalledTimes(1)
    expect(init).toHaveBeenCalledWith(
      expect.objectContaining({
        domain: 'transcribe.test',
        autoCapturePageviews: true,
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
