'use client'

import { useCallback, useEffect, useState } from 'react'
import {
  GovukBody,
  GovukButton,
  GovukButtonGroup,
  GovukFieldset,
  GovukFormGroup,
  GovukHeading,
  GovukHint,
  GovukLabel,
  GovukLegend,
  GovukSelect,
} from '@/components/govuk'
import type { AudioDevice } from '@/components/audio/microphone-permission'
import {
  loadMicrophonePreferences,
  resolveMicrophone,
  saveMicrophonePreferences,
  type MicrophonePreferences,
} from '@/lib/microphone-preferences'

export function MicrophoneSettings({
  userId,
  onSuccess,
}: {
  userId: string
  onSuccess: (message: string | null) => void
}) {
  const [devices, setDevices] = useState<AudioDevice[]>([])
  const [selected, setSelected] = useState<MicrophonePreferences>({
    inPerson: '',
    online: '',
  })
  const [saved, setSaved] = useState<MicrophonePreferences | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [permissionRequired, setPermissionRequired] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [warning, setWarning] = useState<string | null>(null)

  const refreshDevices = useCallback(
    async (requestPermission = false) => {
      try {
        if (requestPermission) {
          const stream = await navigator.mediaDevices?.getUserMedia?.({
            audio: true,
          })
          if (!stream)
            throw new Error(
              'Microphone access is not supported in this browser.'
            )
          stream.getTracks().forEach((track) => track.stop())
        }
        const available = await navigator.mediaDevices?.enumerateDevices?.()
        if (!available)
          throw new Error(
            'Microphone settings are not supported in this browser.'
          )
        const inputs = available.filter(
          (device) => device.kind === 'audioinput'
        )
        if (
          !inputs.length ||
          inputs.some((device) => !device.label || !device.deviceId)
        ) {
          setDevices([])
          setPermissionRequired(true)
          if (requestPermission) {
            setError(
              'No usable microphones were found. Connect a microphone, check your browser permissions and try again.'
            )
          }
          return
        }
        setPermissionRequired(false)
        setDevices(inputs.map(({ deviceId, label }) => ({ deviceId, label })))
        let preferences: MicrophonePreferences
        let preferencesLoaded = true
        try {
          preferences = loadMicrophonePreferences(userId)
        } catch {
          preferences = { inPerson: '', online: '' }
          preferencesLoaded = false
          setSaved(null)
          setError(
            'Your saved microphone settings could not be loaded. Choose and save your microphones again.'
          )
        }
        const inPerson = resolveMicrophone(inputs, preferences.inPerson)
        const online = resolveMicrophone(inputs, preferences.online)
        setSelected({ inPerson: inPerson.deviceId, online: online.deviceId })
        if (!preferencesLoaded) {
          setSaved(null)
        } else if (preferences.inPerson || preferences.online) {
          setSaved(preferences)
        } else {
          setSaved({ inPerson: inPerson.deviceId, online: online.deviceId })
        }
        setWarning(
          inPerson.unavailable || online.unavailable
            ? 'A saved microphone is unavailable. Check and save your selected microphones.'
            : null
        )
      } catch (cause) {
        setDevices([])
        setPermissionRequired(true)
        setError(
          typeof cause === 'object' &&
            cause !== null &&
            'name' in cause &&
            cause.name === 'NotAllowedError'
            ? 'Microphone permission denied. Enable microphone access in your browser settings and try again.'
            : 'Microphone devices could not be loaded. Check your browser supports microphone access and try again.'
        )
      } finally {
        setLoading(false)
      }
    },
    [userId]
  )

  useEffect(() => {
    // Browser device discovery resolves asynchronously; this effect only runs for a new user.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void refreshDevices()
  }, [refreshDevices])

  function requestRefresh(requestPermission = false) {
    setLoading(true)
    setError(null)
    void refreshDevices(requestPermission)
  }

  async function save() {
    if (saving || !devices.length) return
    setSaving(true)
    setError(null)
    onSuccess(null)
    try {
      const available = (
        await navigator.mediaDevices.enumerateDevices()
      ).filter((device) => device.kind === 'audioinput')
      if (
        ![selected.inPerson, selected.online].every((id) =>
          available.some((device) => device.deviceId === id)
        )
      ) {
        setError(
          'A selected microphone is no longer available. Refresh microphones and choose again.'
        )
        return
      }
      try {
        saveMicrophonePreferences(userId, selected)
      } catch {
        setError(
          'Your microphone settings could not be saved. Check your browser allows local storage and try again.'
        )
        return
      }
      setSaved(selected)
      setWarning(null)
      onSuccess('Microphone settings updated')
    } catch {
      setError(
        'Microphone devices could not be checked. Refresh microphones and try again.'
      )
    } finally {
      setSaving(false)
    }
  }

  const unchanged =
    saved?.inPerson === selected.inPerson && saved?.online === selected.online

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault()
        void save()
      }}
    >
      <GovukFieldset
        disabled={loading || saving}
        aria-describedby="microphones-hint"
      >
        <GovukLegend size="m">
          <GovukHeading as="h2" size="m" className="govuk-!-margin-bottom-0">
            Microphone settings
          </GovukHeading>
        </GovukLegend>
        <GovukHint id="microphones-hint">
          The default microphones you would like to use when recording
          conversations
        </GovukHint>
        {loading && <GovukBody role="status">Loading microphones...</GovukBody>}
        {error && (
          <p className="govuk-error-message" role="alert">
            <span className="govuk-visually-hidden">Error:</span> {error}
          </p>
        )}
        {warning && <GovukBody role="status">{warning}</GovukBody>}
        {!loading && permissionRequired && (
          <>
            <GovukBody>
              Allow microphone access to choose your default microphones. These
              settings apply only in this browser.
            </GovukBody>
            <GovukButton type="button" onClick={() => requestRefresh(true)}>
              Allow microphone access
            </GovukButton>
          </>
        )}
        {devices.length > 0 && (
          <>
            {(
              [
                ['inPerson', 'In person'],
                ['online', 'Online'],
              ] as const
            ).map(([context, label]) => (
              <GovukFormGroup key={context}>
                <GovukLabel htmlFor={`microphone-${context}`}>
                  {label}
                </GovukLabel>
                <GovukSelect
                  id={`microphone-${context}`}
                  value={selected[context]}
                  onChange={(event) => {
                    onSuccess(null)
                    setSelected({ ...selected, [context]: event.target.value })
                  }}
                >
                  {devices.map((device) => (
                    <option key={device.deviceId} value={device.deviceId}>
                      {device.label}
                    </option>
                  ))}
                </GovukSelect>
              </GovukFormGroup>
            ))}
            <GovukButtonGroup>
              <GovukButton
                type="submit"
                disabled={unchanged || saving}
                variant={unchanged || saving ? 'secondary' : 'primary'}
              >
                {saving ? 'Saving microphones...' : 'Save microphones'}
              </GovukButton>
              <GovukButton
                type="button"
                variant="secondary"
                onClick={() => requestRefresh()}
              >
                Refresh microphones
              </GovukButton>
            </GovukButtonGroup>
          </>
        )}
      </GovukFieldset>
    </form>
  )
}
