import { describe, it, expect } from 'vitest'
import { formatTranscript, preprocessHtml } from '@/lib/download-word-doc'

const TEST_TRANSCRIPT = [
  { speaker: 'Alice', text: 'Hello', start_time: 0, end_time: 1 },
  { speaker: 'Bob', text: 'Hi', start_time: 1, end_time: 2 },
]

describe('formatTranscript', () => {
  it('formats entries correctly', () => {
    const result = formatTranscript(TEST_TRANSCRIPT)

    expect(result).toContain('<strong>Alice</strong>: Hello')
    expect(result).toContain('<strong>Bob</strong>: Hi')
    expect(result).toContain('<p>&nbsp;</p>')
  })

  it('handles empty transcript', () => {
    expect(formatTranscript([])).toBe('')
  })
})

describe('preprocessHtml', () => {
  it('replaces <br> with paragraph breaks', () => {
    const html = '<p>Hello<br>World</p>'
    const result = preprocessHtml(html, [])

    expect(result).toContain('</p><p>')
  })

  it('normalises empty paragraphs', () => {
    const html = '<p></p>'
    const result = preprocessHtml(html, [])

    expect(result).toContain('<p>&nbsp;</p>')
  })

  it('includes transcript section', () => {
    const result = preprocessHtml('<p>Hi</p>', TEST_TRANSCRIPT)

    expect(result).toContain('Meeting Transcript:')
    expect(result).toContain('<strong>Alice</strong>: Hello')
    expect(result).toContain('<strong>Bob</strong>: Hi')
  })
})
