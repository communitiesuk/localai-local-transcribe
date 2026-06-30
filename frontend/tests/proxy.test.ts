import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { NextRequest } from 'next/server'

vi.mock('@/utils/auth', () => ({
  createAlbJwtVerifier: vi.fn(() => ({ verify: vi.fn() })),
  parseAuthToken: vi.fn(),
}))

const { parseAuthToken } = await import('@/utils/auth')
const { proxy } = await import('@/proxy')

const buildRequest = (headers: Record<string, string> = {}) =>
  new NextRequest(new URL('https://example.com/some-page'), { headers })

beforeEach(() => {
  vi.mocked(parseAuthToken).mockReset()
})

afterEach(() => {
  vi.unstubAllEnvs()
  vi.unstubAllGlobals()
})

describe('proxy auth pathways', () => {
  it('bypasses auth when ENVIRONMENT is local', async () => {
    vi.stubEnv('ENVIRONMENT', 'local')
    vi.stubEnv('BACKEND_HOST', 'http://local')
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(new Response(null, { status: 200 }))
    )

    const res = await proxy(buildRequest())

    expect(res.headers.get('x-middleware-next')).toBe('1')
    expect(parseAuthToken).not.toHaveBeenCalled()
  })

  it('redirects to /unauthorised when auth token is missing', async () => {
    vi.stubEnv('ENVIRONMENT', 'development')
    vi.stubEnv('BACKEND_HOST', 'http://development')
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(new Response(null, { status: 200 }))
    )

    const res = await proxy(buildRequest())

    expect(res.status).toBe(307)
    expect(res.headers.get('location')).toBe('https://example.com/unauthorised')
    expect(parseAuthToken).not.toHaveBeenCalled()
  })

  it('proceeds when parseAuthToken returns an authorised result', async () => {
    vi.stubEnv('ENVIRONMENT', 'development')
    vi.stubEnv('BACKEND_HOST', 'http://development')
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(new Response(null, { status: 200 }))
    )
    vi.mocked(parseAuthToken).mockResolvedValue({
      email: 'a@b.com',
      isAuthorised: true,
      authReason: 'OIDC',
    })

    const res = await proxy(buildRequest({ 'x-amzn-oidc-data': 'tok' }))

    expect(res.headers.get('x-middleware-next')).toBe('1')
    expect(parseAuthToken).toHaveBeenCalledWith(expect.anything(), 'tok')
  })

  it('redirects to /unauthorised when parseAuthToken returns null', async () => {
    vi.stubEnv('ENVIRONMENT', 'development')
    vi.stubEnv('BACKEND_HOST', 'http://development')
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(new Response(null, { status: 200 }))
    )
    vi.mocked(parseAuthToken).mockResolvedValue(null)

    const res = await proxy(buildRequest({ 'x-amzn-oidc-data': 'tok' }))

    expect(res.status).toBe(307)
    expect(res.headers.get('location')).toBe('https://example.com/unauthorised')
  })

  it('redirects to /unauthorised when parseAuthToken returns isAuthorised: false', async () => {
    vi.stubEnv('ENVIRONMENT', 'development')
    vi.stubEnv('BACKEND_HOST', 'http://development')
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(new Response(null, { status: 200 }))
    )
    vi.mocked(parseAuthToken).mockResolvedValue({
      email: 'a@b.com',
      isAuthorised: false,
      authReason: 'OIDC',
    })

    const res = await proxy(buildRequest({ 'x-amzn-oidc-data': 'tok' }))

    expect(res.status).toBe(307)
    expect(res.headers.get('location')).toBe('https://example.com/unauthorised')
  })

  it('redirects to /generic-error when parseAuthToken throws', async () => {
    vi.stubEnv('ENVIRONMENT', 'development')
    vi.stubEnv('BACKEND_HOST', 'http://development')
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(new Response(null, { status: 200 }))
    )
    vi.mocked(parseAuthToken).mockRejectedValue(new Error('boom'))

    const res = await proxy(buildRequest({ 'x-amzn-oidc-data': 'tok' }))

    expect(res.status).toBe(307)
    expect(res.headers.get('location')).toBe(
      'https://example.com/generic-error'
    )
  })

  it('redirects to /unauthorised when the backend returns 401', async () => {
    vi.stubEnv('ENVIRONMENT', 'development')
    vi.stubEnv('BACKEND_HOST', 'http://development')
    vi.mocked(parseAuthToken).mockResolvedValue({
      email: 'a@b.com',
      isAuthorised: true,
      authReason: 'OIDC',
    })
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(new Response(null, { status: 401 }))
    )

    const res = await proxy(buildRequest({ 'x-amzn-oidc-data': 'tok' }))

    expect(res.status).toBe(307)
    expect(res.headers.get('location')).toBe('https://example.com/unauthorised')
  })
})
