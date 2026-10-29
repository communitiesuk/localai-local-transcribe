import { describe, expect, it } from 'vitest'
import { getSafeDestination } from '@/hooks/use-destination'

describe('getSafeDestination', () => {
  it.each(['/templates', '/settings?tab=profile', '/templates#section'])(
    'returns the same-site path %s unchanged',
    (destination) => {
      expect(getSafeDestination(destination)).toBe(destination)
    }
  )

  it('strips the origin from an absolute URL on this site', () => {
    expect(
      getSafeDestination(`${window.location.origin}/settings?tab=profile`)
    ).toBe('/settings?tab=profile')
  })

  it.each([
    'https://evil.example',
    '//evil.example',
    '/\\evil.example',
    'http://localhost:4000/templates',
  ])('returns null for the external destination %s', (destination) => {
    expect(getSafeDestination(destination)).toBeNull()
  })

  it('returns null for an invalid URL', () => {
    expect(getSafeDestination('http://[')).toBeNull()
  })
})
