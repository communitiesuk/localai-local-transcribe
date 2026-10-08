import type { AudioDevice } from '@/components/audio/microphone-permission'

export function microphoneInUse(
  devices: AudioDevice[],
  micStream: MediaStream | null
): string | undefined {
  const track = micStream?.getAudioTracks()[0]
  if (!track) {
    return undefined
  }

  const { deviceId } = track.getSettings()
  const inUse = devices.find((device) => device.deviceId === deviceId)
  return inUse?.label || track.label || undefined
}
