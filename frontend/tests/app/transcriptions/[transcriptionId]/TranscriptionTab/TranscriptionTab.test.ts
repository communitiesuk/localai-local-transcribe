import { describe, it, expect } from 'vitest'
import {
  isEntryPlaying,
  buildTranscriptionHtml,
} from '@/app/transcriptions/[transcriptionId]/TranscriptionTab/TranscriptionTab'
import { DialogueEntry } from '@/lib/client'

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

describe('buildTranscriptionHtml', () => {
  const mockTranscript: DialogueEntry[] = [
    { speaker: 'Alice', text: 'Hello', start_time: 0, end_time: 1 },
    { speaker: 'Bob', text: 'Hi', start_time: 1, end_time: 2 },
  ]

  it('formats a single entry', () => {
    const result = buildTranscriptionHtml(mockTranscript.slice(0, 1))

    expect(result).toBe('<p><b>Alice:</b> Hello</p>')
  })

  it('formats multiple entries with spacing', () => {
    const result = buildTranscriptionHtml(mockTranscript)

    expect(result).toBe('<p><b>Alice:</b> Hello</p>\n\n<p><b>Bob:</b> Hi</p>')
  })

  it('returns empty string for no entries', () => {
    expect(buildTranscriptionHtml([])).toBe('')
  })

  it('handles undefined input', () => {
    expect(buildTranscriptionHtml(undefined as any)).toBe('')
  })
})
