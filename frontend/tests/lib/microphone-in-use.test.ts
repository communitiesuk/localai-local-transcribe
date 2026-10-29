import { describe, expect, it } from 'vitest'

import { microphoneInUse } from '@/lib/microphone-in-use'

const devices = [
  { deviceId: 'default', label: 'Default - External Microphone (Built-in)' },
  { deviceId: 'headset', label: 'Headset Microphone' },
]

const streamWith = (deviceId?: string, label = '') =>
  ({
    getAudioTracks: () => [
      { getSettings: () => ({ deviceId }), label } as MediaStreamTrack,
    ],
  }) as unknown as MediaStream

const streamWithNoTracks = () =>
  ({ getAudioTracks: () => [] }) as unknown as MediaStream

describe('microphoneInUse', () => {
  it('names the device the track is actually recording from', () => {
    expect(microphoneInUse(devices, streamWith('headset'))).toBe(
      'Headset Microphone'
    )
  })

  it('names the fallback device when the browser did not grant the requested one', () => {
    expect(microphoneInUse(devices, streamWith('default'))).toBe(
      'Default - External Microphone (Built-in)'
    )
  })

  it('falls back to the track label when the device is not in the list', () => {
    expect(microphoneInUse(devices, streamWith('unplugged', 'USB Mic'))).toBe(
      'USB Mic'
    )
  })

  it('falls back to the track label when the browser reports no device id', () => {
    expect(microphoneInUse(devices, streamWith(undefined, 'USB Mic'))).toBe(
      'USB Mic'
    )
  })

  it('returns nothing when there is no stream, so no empty line is shown', () => {
    expect(microphoneInUse(devices, null)).toBeUndefined()
  })

  it('returns nothing when the stream has no audio track', () => {
    expect(microphoneInUse(devices, streamWithNoTracks())).toBeUndefined()
  })

  it('returns nothing when neither the device nor the track has a label', () => {
    expect(microphoneInUse([], streamWith('quiet'))).toBeUndefined()
  })
})
