import { describe, it, expect } from 'vitest'
import { getPageNumbers } from '@/components/recent-meetings/paginated-transcriptions'

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
