import { describe, expect, it, vi } from 'vitest'
import { parseAuthToken, type JwtPayloadVerifier } from '@/utils/auth'

const fakeVerifier = (
  impl: (token: string) => Promise<unknown>
): JwtPayloadVerifier => ({ verify: vi.fn(impl) })

describe('parseAuthToken', () => {
  it('returns null when token is empty', async () => {
    const verifier = fakeVerifier(async () => ({ email: 'a@b.com' }))
    expect(await parseAuthToken(verifier, '')).toBeNull()
    expect(verifier.verify).not.toHaveBeenCalled()
  })

  it('returns authorised result when verifier resolves with an email', async () => {
    const verifier = fakeVerifier(async () => ({ email: 'a@b.com' }))
    expect(await parseAuthToken(verifier, 'tok')).toEqual({
      email: 'a@b.com',
      isAuthorised: true,
      authReason: 'OIDC',
    })
  })

  it('returns null when verifier rejects', async () => {
    const verifier = fakeVerifier(async () => {
      throw new Error('bad signature')
    })
    expect(await parseAuthToken(verifier, 'tok')).toBeNull()
  })

  it('returns null when payload has no email', async () => {
    const verifier = fakeVerifier(async () => ({}))
    expect(await parseAuthToken(verifier, 'tok')).toBeNull()
  })
})
