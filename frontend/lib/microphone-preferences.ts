import type { AudioDevice } from '@/components/audio/microphone-permission'

export type MicrophonePreferences = { inPerson: string; online: string }
export type MicrophoneContext = keyof MicrophonePreferences

const storageKey = (userId: string) =>
  `local-transcribe:microphones:v1:${userId}`

export function loadMicrophonePreferences(
  userId: string
): MicrophonePreferences {
  const stored = localStorage.getItem(storageKey(userId))
  if (!stored) return { inPerson: '', online: '' }
  const value: unknown = JSON.parse(stored)
  if (
    typeof value !== 'object' ||
    value === null ||
    !('inPerson' in value) ||
    !('online' in value) ||
    typeof value.inPerson !== 'string' ||
    typeof value.online !== 'string'
  ) {
    throw new Error(
      'Saved microphone settings are invalid. Choose and save your microphones again.'
    )
  }
  return { inPerson: value.inPerson, online: value.online }
}

export function saveMicrophonePreferences(
  userId: string,
  preferences: MicrophonePreferences
) {
  localStorage.setItem(storageKey(userId), JSON.stringify(preferences))
}

export function resolveMicrophone(
  devices: AudioDevice[],
  preferredId: string
): { deviceId: string; unavailable: boolean } {
  const preferred = devices.find((device) => device.deviceId === preferredId)
  return {
    deviceId:
      preferred?.deviceId ??
      devices.find((device) => device.deviceId === 'default')?.deviceId ??
      devices[0]?.deviceId ??
      '',
    unavailable: !!preferredId && !preferred,
  }
}
