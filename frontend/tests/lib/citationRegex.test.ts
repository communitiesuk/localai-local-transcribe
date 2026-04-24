import { describe, it, expect, beforeEach } from 'vitest'
import { citationRegex, citationRegexWithSpace } from '@/lib/citationRegex'

describe('citationRegex', () => {
  it('matches a simple citation', () => {
    expect('[1]').toMatch(citationRegex)
  })

  it('matches a citation with a range', () => {
    expect('[1-3]').toMatch(citationRegex)
  })

  it('captures the citation number', () => {
    const match = '[42]'.match(citationRegex)
    expect(match?.[1]).toBe('42')
  })

  it('does not match text without brackets', () => {
    expect('hello world').not.toMatch(citationRegex)
  })

  it('does not match unbalanced brackets', () => {
    expect('[1').not.toMatch(citationRegex)
    expect('1]').not.toMatch(citationRegex)
  })

  it('does not match non-numeric content in brackets', () => {
    expect('[abc]').not.toMatch(citationRegex)
  })
})

describe('citationRegexWithSpace', () => {
  beforeEach(() => {
    citationRegexWithSpace.lastIndex = 0
  })

  it('matches a citation preceded by a space', () => {
    const matches = ' [1]'.match(citationRegexWithSpace)
    expect(matches).not.toBeNull()
  })

  it('matches a citation without a preceding space', () => {
    const matches = '[2]'.match(citationRegexWithSpace)
    expect(matches).not.toBeNull()
  })

  it('matches a citation with a range', () => {
    const matches = ' [3-5]'.match(citationRegexWithSpace)
    expect(matches).not.toBeNull()
  })

  it('matches multiple citations in a string', () => {
    const matches = 'text [1] more [2-4] end'.match(citationRegexWithSpace)
    expect(matches).toHaveLength(2)
  })

  it('captures the optional leading space', () => {
    const match = citationRegexWithSpace.exec(' [7]')
    citationRegexWithSpace.lastIndex = 0
    expect(match?.[1]).toBe(' ')
  })

  it('captures an empty string when there is no leading space', () => {
    const match = citationRegexWithSpace.exec('[7]')
    citationRegexWithSpace.lastIndex = 0
    expect(match?.[1]).toBe('')
  })

  it('captures the citation number', () => {
    const match = citationRegexWithSpace.exec('[99]')
    citationRegexWithSpace.lastIndex = 0
    expect(match?.[2]).toBe('99')
  })
})
