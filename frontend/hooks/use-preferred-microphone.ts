import { useQuery } from '@tanstack/react-query'
import { getUserUsersMeGetOptions } from '@/lib/client/@tanstack/react-query.gen'
import type { AudioDevice } from '@/components/audio/microphone-permission'
import {
  loadMicrophonePreferences,
  resolveMicrophone,
  type MicrophoneContext,
} from '@/lib/microphone-preferences'

export function usePreferredMicrophone(context: MicrophoneContext) {
  const { data: user, isPending } = useQuery(getUserUsersMeGetOptions())

  const resolve = (devices: AudioDevice[]) => {
    try {
      if (!user) throw new Error('User settings are unavailable')
      const preferences = loadMicrophonePreferences(user.id)
      const selection = resolveMicrophone(devices, preferences[context])
      return {
        deviceId: selection.deviceId,
        warning: selection.unavailable
          ? 'Your saved microphone is unavailable. Check the selected microphone before recording.'
          : null,
      }
    } catch {
      return {
        deviceId: resolveMicrophone(devices, '').deviceId,
        warning:
          'Your microphone settings could not be loaded. Check the selected microphone before recording.',
      }
    }
  }
  return { isReady: !isPending, resolve }
}
