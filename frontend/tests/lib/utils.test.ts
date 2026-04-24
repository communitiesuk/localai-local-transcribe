import { describe, it, expect } from 'vitest'
import { cn } from '@/lib/utils'

describe('cn', () => {
  it('merges simple classes', () => {
    expect(cn('p-2', 'text-sm')).toBe('p-2 text-sm')
  })

  it('resolves tailwind conflicts', () => {
    expect(cn('p-2', 'p-4')).toBe('p-4')
  })

  it('handles conditional classes', () => {
    expect(cn('p-2', false && 'hidden')).toBe('p-2')
  })
})
