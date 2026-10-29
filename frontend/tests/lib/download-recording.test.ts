import { describe, expect, it, vi } from 'vitest'
import { saveAs } from 'file-saver'

import {
  downloadRecording,
  getRecordingFileName,
} from '@/lib/download-recording'

vi.mock('file-saver', () => ({
  saveAs: vi.fn(),
}))

describe('getRecordingFileName', () => {
  it('names the file after the time the recording started', () => {
    const file = new Blob(['audio'], { type: 'audio/webm' })

    expect(getRecordingFileName(file, new Date(2026, 9, 2, 9, 5, 3))).toBe(
      'local-transcribe-recording-2026-10-02-090503.webm'
    )
  })

  it('takes the extension from the recording itself', () => {
    const file = new Blob(['audio'], { type: 'video/mp4' })

    expect(getRecordingFileName(file, new Date(2026, 9, 2, 9, 5, 3))).toBe(
      'local-transcribe-recording-2026-10-02-090503.mp4'
    )
  })

  it('falls back to the current time when the start time is unknown', () => {
    const file = new Blob(['audio'], { type: 'audio/webm' })

    expect(getRecordingFileName(file)).toMatch(
      /^local-transcribe-recording-\d{4}-\d{2}-\d{2}-\d{6}\.webm$/
    )
  })
})

describe('downloadRecording', () => {
  it('saves the recording under its generated name', () => {
    const file = new Blob(['audio'], { type: 'audio/webm' })

    downloadRecording(file, new Date(2026, 9, 2, 9, 5, 3))

    expect(saveAs).toHaveBeenCalledWith(
      file,
      'local-transcribe-recording-2026-10-02-090503.webm'
    )
  })
})
