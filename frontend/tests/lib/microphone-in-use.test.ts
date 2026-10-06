import { describe, expect, it } from 'vitest'

import { microphoneInUse } from '@/lib/microphone-in-use'

const devices = [
  { deviceId: 'default', label: 'Default - External Microphone (Built-in)' },
  { deviceId: 'headset', label: 'Headset Microphone' },
]

describe('microphoneInUse', () => {
  it('names the device that was selected', () => {
    expect(microphoneInUse(devices, 'headset')).toBe('Headset Microphone')
  })

  it('falls back to the first device when the selection is not in the list', () => {
    expect(microphoneInUse(devices, 'unplugged')).toBe(
      'Default - External Microphone (Built-in)'
    )
  })

  it('returns nothing when there are no devices, so no empty line is shown', () => {
    expect(microphoneInUse([], 'headset')).toBeUndefined()
  })

  it('returns nothing when the device has no label', () => {
    expect(
      microphoneInUse([{ deviceId: 'quiet', label: '' }], 'quiet')
    ).toBeUndefined()
  })
})
