import { describe, expect, it } from 'vitest'
import validateEmail, {
  EMAIL_FORMAT_MESSAGE,
  EMAIL_LENGTH_MESSAGE,
  EMAIL_LOCAL_PART_LENGTH_MESSAGE,
  EMAIL_MISSING_MESSAGE,
} from '@/utils/validate-email'

describe('validateEmail', () => {
  it('accepts an ordinary address', () => {
    expect(validateEmail('test.user@example.gov.uk')).toBeNull()
  })

  it('accepts a subdomain', () => {
    expect(validateEmail('test.user@mail.example.gov.uk')).toBeNull()
  })

  it('asks for an address when there is nothing to check', () => {
    expect(validateEmail('')).toBe(EMAIL_MISSING_MESSAGE)
  })

  it.each([
    'test.user',
    'test.user@',
    '@example.gov.uk',
    'test user@example.gov.uk',
    'test.user@example',
    'test.user@@example.gov.uk',
    'test.user@example..gov.uk',
  ])('rejects %s as malformed', (email) => {
    expect(validateEmail(email)).toBe(EMAIL_FORMAT_MESSAGE)
  })

  it('rejects a local part longer than 64 characters', () => {
    const email = `${'a'.repeat(65)}@example.gov.uk`

    expect(validateEmail(email)).toBe(EMAIL_LOCAL_PART_LENGTH_MESSAGE)
  })

  it('accepts a local part of exactly 64 characters', () => {
    const email = `${'a'.repeat(64)}@example.gov.uk`

    expect(validateEmail(email)).toBeNull()
  })

  it('rejects an address longer than 254 characters', () => {
    const domain = `${'b'.repeat(240)}.gov.uk`
    const email = `${'a'.repeat(10)}@${domain}`

    expect(email.length).toBeGreaterThan(254)
    expect(validateEmail(email)).toBe(EMAIL_LENGTH_MESSAGE)
  })
})
