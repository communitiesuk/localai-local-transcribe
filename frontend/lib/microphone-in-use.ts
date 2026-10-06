import type { AudioDevice } from '@/components/audio/microphone-permission'

export function microphoneInUse(
  devices: AudioDevice[],
  selectedDeviceId: string
): string | undefined {
  const selected = devices.find(
    (device) => device.deviceId === selectedDeviceId
  )
  return (selected ?? devices[0])?.label || undefined
}
