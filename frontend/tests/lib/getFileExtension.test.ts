import { describe, it, expect } from 'vitest'
import {
  getFileExtension,
  getFileExtensionFromBlob,
} from '@/lib/getFileExtension'

describe('getFileExtension', () => {
  it('returns extension for normal file', () => {
    expect(getFileExtension('song.mp3')).toBe('mp3')
  })

  it('handles multiple dots', () => {
    expect(getFileExtension('archive.tar.gz')).toBe('gz')
  })

  it('returns empty string if no dot', () => {
    expect(getFileExtension('README')).toBe('')
  })

  it('handles hidden files', () => {
    expect(getFileExtension('.env')).toBe('env')
  })

  it('handles empty string', () => {
    expect(getFileExtension('')).toBe('')
  })
})

describe('getFileExtensionFromBlob', () => {
  it('returns mapped audio extension', () => {
    const blob = new Blob([], { type: 'audio/mpeg' })
    expect(getFileExtensionFromBlob(blob)).toBe('mp3')
  })

  it('returns mapped video extension', () => {
    const blob = new Blob([], { type: 'video/mp4' })
    expect(getFileExtensionFromBlob(blob)).toBe('mp4')
  })

  it('removes codec information', () => {
    const blob = new Blob([], { type: 'audio/webm;codecs=opus' })
    expect(getFileExtensionFromBlob(blob)).toBe('webm')
  })

  it('returns media for non-audio/video types', () => {
    const blob = new Blob([], { type: 'image/png' })
    expect(getFileExtensionFromBlob(blob)).toBe('media')
  })

  it('returns media if type is empty', () => {
    const blob = new Blob([], { type: '' })
    expect(getFileExtensionFromBlob(blob)).toBe('media')
  })

  it('falls back to subtype if not mapped', () => {
    const blob = new Blob([], { type: 'audio/flac' })
    expect(getFileExtensionFromBlob(blob)).toBe('flac')
  })
})
