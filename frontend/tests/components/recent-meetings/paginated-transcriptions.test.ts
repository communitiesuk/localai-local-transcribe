import { describe, it, expect } from 'vitest'
import {
  formatDateOfBirth,
  getPageNumbers,
} from '@/components/recent-meetings/paginated-labelled-transcriptions'

describe('formatDateOfBirth', () => {
  it('formats a timestamp as DD/MM/YYYY without the time', () => {
    expect(formatDateOfBirth('1985-04-12T00:00:00')).toBe('12/04/1985')
    expect(formatDateOfBirth('1985-04-12T00:00:00.000Z')).toBe('12/04/1985')
  })

  it('formats a plain date as DD/MM/YYYY', () => {
    expect(formatDateOfBirth('1985-04-12')).toBe('12/04/1985')
  })

  it('shows a dash when there is no date of birth', () => {
    expect(formatDateOfBirth(null)).toBe('—')
    expect(formatDateOfBirth(undefined)).toBe('—')
  })
})

describe('getPageNumbers', () => {
  it('returns first pages when current page is near start', () => {
    expect(getPageNumbers(1, 10)).toEqual([1, 2, 3, 4, 5])
    expect(getPageNumbers(2, 10)).toEqual([1, 2, 3, 4, 5])
  })

  it('centers current page when in middle', () => {
    expect(getPageNumbers(5, 10)).toEqual([3, 4, 5, 6, 7])
  })

  it('returns last pages when current page is near end', () => {
    expect(getPageNumbers(9, 10)).toEqual([6, 7, 8, 9, 10])
    expect(getPageNumbers(10, 10)).toEqual([6, 7, 8, 9, 10])
  })

  it('handles totalPages less than maxPagesToShow', () => {
    expect(getPageNumbers(1, 3)).toEqual([1, 2, 3])
    expect(getPageNumbers(2, 3)).toEqual([1, 2, 3])
  })

  it('handles single page', () => {
    expect(getPageNumbers(1, 1)).toEqual([1])
  })
})
