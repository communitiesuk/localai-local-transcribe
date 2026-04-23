import { describe, it, expect } from 'vitest'
import { isEntryPlaying } from '@/app/transcriptions/[transcriptionId]/TranscriptionTab/TranscriptionTab'

describe('isEntryPlaying', () => {
  it('returns false when time is before entry start', () => {
    expect(isEntryPlaying(4, 5, 10)).toBe(false)
  })

  it('returns true when time equals entry start', () => {
    expect(isEntryPlaying(5, 5, 10)).toBe(true)
  })

  it('returns true when time is between entry and next entry', () => {
    expect(isEntryPlaying(7, 5, 10)).toBe(true)
  })

  it('returns false when time equals next entry start', () => {
    expect(isEntryPlaying(10, 5, 10)).toBe(false)
  })

  it('returns false when time is after next entry start', () => {
    expect(isEntryPlaying(12, 5, 10)).toBe(false)
  })

  it('handles last entry', () => {
    expect(isEntryPlaying(100, 5)).toBe(true)
  })

  it('handles last entry with time before start', () => {
    expect(isEntryPlaying(3, 5)).toBe(false)
  })
})
