import { describe, expect, it } from 'vitest'
import { getInviteErrorMessage } from '@/app/invite-user/confirm/page'

const GENERIC_MESSAGE = 'Could not send the invitation. Try again.'

describe('getInviteErrorMessage', () => {
  it('returns the specific detail thrown by the client', () => {
    const error = {
      detail:
        'This evaluation ID is already in use. Check the evaluation ID you received from MHCLG.',
    }

    expect(getInviteErrorMessage(error)).toBe(
      'This evaluation ID is already in use. Check the evaluation ID you received from MHCLG.'
    )
  })

  it('falls back to the generic message when there is no detail', () => {
    expect(getInviteErrorMessage(new Error('network failure'))).toBe(
      GENERIC_MESSAGE
    )
  })

  it('falls back to the generic message when the detail is not a string', () => {
    expect(getInviteErrorMessage({ detail: [{ msg: 'bad' }] })).toBe(
      GENERIC_MESSAGE
    )
  })

  it('falls back to the generic message for null', () => {
    expect(getInviteErrorMessage(null)).toBe(GENERIC_MESSAGE)
  })
})
