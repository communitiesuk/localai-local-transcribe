'use client'

// frontend/components/audio/microphone-permission.tsx
import { GovukButton } from '@/components/govuk'
import { Loader2 } from 'lucide-react'
import React, { useCallback, useEffect, useState } from 'react'

interface MicrophonePermissionProps {
  onPermissionGranted: (devices: AudioDevice[]) => void
  onError: (error: string) => void
}

export interface AudioDevice {
  deviceId: string
  label: string
}

export function MicrophonePermission({
  onPermissionGranted,
  onError,
}: MicrophonePermissionProps) {
  const [permissionDenied, setPermissionDenied] = useState(false)
  const [isRequesting, setIsRequesting] = useState(true)

  const getAudioDevices = useCallback(async () => {
    try {
      const devices = await navigator.mediaDevices.enumerateDevices()
      const audioInputDevices = devices
        .filter((device) => device.kind === 'audioinput')
        .map((device) => ({
          deviceId: device.deviceId,
          label: device.label || `Microphone ${device.deviceId.slice(0, 5)}`,
        }))

      if (audioInputDevices.length > 0) {
        onPermissionGranted(audioInputDevices)
      }
    } catch {
      onError('Error getting audio devices')
      setPermissionDenied(true)
      setIsRequesting(false)
    }
  }, [onError, onPermissionGranted])

  const requestMicrophonePermission = useCallback(async () => {
    setIsRequesting(true)
    setPermissionDenied(false)

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      stream.getTracks().forEach((track) => track.stop())
      await getAudioDevices()
    } catch {
      onError(
        'Microphone permission denied. Please enable it in your browser settings.'
      )
      setPermissionDenied(true)
      setIsRequesting(false)
    }
  }, [getAudioDevices, onError])

  useEffect(() => {
    // requestMicrophonePermission sets state synchronously before its first await,
    // which the linter flags as a cascading render risk. This is acceptable here —
    // the effect only re-runs if onError or onPermissionGranted change, and the
    // synchronous setState (setIsRequesting/setPermissionDenied) is a trivial
    // UI state reset, not an expensive cascading render.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    requestMicrophonePermission()
  }, [requestMicrophonePermission])

  return (
    <div>
      {permissionDenied ? (
        <p className="govuk-error-message" role="alert">
          <span className="govuk-visually-hidden">Error:</span> Microphone
          permission denied. Please enable it in your browser settings.
        </p>
      ) : (
        <div className="govuk-inset-text">
          <p className="govuk-body flex items-center gap-2">
            {isRequesting && (
              <Loader2
                className="mr-2 size-4 animate-spin"
                aria-hidden="true"
              />
            )}
            {isRequesting
              ? 'Requesting microphone access...'
              : 'Microphone permission is required to use this feature.'}
          </p>
        </div>
      )}
      {permissionDenied && (
        <GovukButton
          type="button"
          onClick={requestMicrophonePermission}
          className="govuk-!-margin-top-2"
        >
          Request Microphone Permission
        </GovukButton>
      )}
    </div>
  )
}
