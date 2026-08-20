'use client'

import { useCallback, useEffect, useRef, useState } from 'react'

import { GovukButton, GovukFormGroup, GovukLabel } from '@/components/govuk'

import { DiscardConfirmDialog } from '@/components/audio/discard-dialog'
import {
  AudioDevice,
  MicrophonePermission,
} from '@/components/audio/microphone-permission'
import RecordingControl from '@/components/audio/recording-control'
import { StartTranscriptionSection } from '@/components/audio/start-transcription-section'
import { TranscriptionForm } from '@/components/audio/types'
import { useTabCloseWarning } from '@/hooks/use-tab-close-warning'
import { useWakeLock } from '@/hooks/use-wake-lock'
import { useStartTranscription } from '@/hooks/useStartTranscription'
import { useRecordingDb } from '@/providers/transcription-db-provider'
import { Controller, FormProvider, useFormContext } from 'react-hook-form'
import AudioPlayerComponent from '../audio-player'
import { useRecordingUiStore } from '@/stores/use-recording-ui-store'
import { RecordingLoading } from '@/components/recording-loading'
import { useCountdown } from '@/hooks/use-countdown'

export const TabRecorderForm = () => {
  const { isPending, onSubmit, form } = useStartTranscription()
  const watchBlob = form.watch('file')

  return (
    <FormProvider {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)}>
        <Controller
          control={form.control}
          name="file"
          render={({ field: { onChange, value } }) => (
            <TabRecorder
              recordedAudio={value}
              setRecordedAudio={(blob) => onChange(blob)}
            />
          )}
        />
        <StartTranscriptionSection
          isShowing={!!watchBlob}
          isPending={isPending}
        />
      </form>
    </FormProvider>
  )
}

function TabRecorder({
  setRecordedAudio,
  recordedAudio,
}: {
  recordedAudio: Blob | null
  setRecordedAudio: (blob: Blob | null) => void
}) {
  const { requestWakeLock, releaseWakeLock } = useWakeLock()
  const { updateRecording, addRecording, removeRecording } = useRecordingDb()
  const [err, setError] = useState<string | null>(null)
  const [isRecording, setIsRecording] = useState(false)
  const [discardDialogOpen, setDiscardDialogOpen] = useState(false)
  const audioContext = useRef<AudioContext | null>(null)
  const recordingGain = useRef<GainNode | null>(null)
  const form = useFormContext<TranscriptionForm>()
  const [selectedDeviceId, setSelectedDeviceId] = useState<string>('')
  const [permissionGranted, setPermissionGranted] = useState<boolean>(false)
  const [audioDevices, setAudioDevices] = useState<AudioDevice[]>([])
  const handlePermissionGranted = (devices: AudioDevice[]) => {
    setAudioDevices(devices)
    setSelectedDeviceId(devices[0].deviceId)
    setPermissionGranted(true)
    setError(null)
  }
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const mediaChunksRef = useRef<Blob[]>([])
  const isStartingRecordingRef = useRef(false)
  const streamRef = useRef<MediaStream | null>(null)
  const screenStreamRef = useRef<MediaStream | null>(null)
  const micStreamRef = useRef<MediaStream | null>(null)
  const [stream, setStream] = useState<MediaStream | null>(null)

  const setRecordingUIState = useRecordingUiStore(
    (state) => state.setRecordingState
  )

  useTabCloseWarning(isRecording || !!recordedAudio)

  const stopAllTracks = useCallback(() => {
    isStartingRecordingRef.current = false

    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => {
        track.stop()
      })
    }
    if (screenStreamRef.current) {
      screenStreamRef.current.getTracks().forEach((track) => track.stop())
    }
    if (micStreamRef.current) {
      micStreamRef.current.getTracks().forEach((track) => track.stop())
    }
    streamRef.current = null
    screenStreamRef.current = null
    micStreamRef.current = null
    mediaRecorderRef.current = null
    setStream(null)

    setIsRecording(false)
    releaseWakeLock()
  }, [releaseWakeLock])

  const stopRecording = useCallback(() => {
    if (!mediaRecorderRef.current || !isRecording) {
      return
    }
    try {
      if (mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop()
      } else {
        stopAllTracks()
      }
    } catch {
      stopAllTracks()
    }
  }, [isRecording, stopAllTracks])

  useEffect(() => {
    return () => {
      stopRecording()
    }
  }, [stopRecording])

  useEffect(() => {
    return () => {
      if (audioContext.current) {
        audioContext.current.close().catch(console.error)
      }
    }
  }, [])

  const handlePauseStateChange = useCallback((paused: boolean) => {
    if (!mediaRecorderRef.current) {
      return
    }
    if (paused) {
      mediaRecorderRef.current.pause()
    } else {
      mediaRecorderRef.current.resume()
    }
  }, [])

  const startRecording = useCallback(async () => {
    // prevent start recording triggering multiple times if recording has already started
    if (
      isStartingRecordingRef.current ||
      mediaRecorderRef.current?.state === 'recording' ||
      mediaRecorderRef.current?.state === 'paused'
    ) {
      return
    }

    isStartingRecordingRef.current = true

    setError(null)
    mediaChunksRef.current = []

    try {
      const screenStream = screenStreamRef.current

      if (!screenStream) {
        throw new Error('No tab or window was selected for recording.')
      }

      const newAudioContext = new AudioContext()
      const destination = newAudioContext.createMediaStreamDestination()
      audioContext.current = newAudioContext

      const gainNode = newAudioContext.createGain()
      gainNode.gain.value = 1.0
      recordingGain.current = gainNode

      const screenSource = newAudioContext.createMediaStreamSource(screenStream)
      const screenGain = newAudioContext.createGain()
      screenGain.gain.value = 1.0
      screenSource.connect(screenGain).connect(gainNode).connect(destination)

      try {
        const micStream = await navigator.mediaDevices.getUserMedia({
          audio: { deviceId: selectedDeviceId },
        })
        micStreamRef.current = micStream
        const micSource = newAudioContext.createMediaStreamSource(micStream)
        const micGain = newAudioContext.createGain()
        micGain.gain.value = 1.0
        micSource.connect(micGain).connect(gainNode).connect(destination)
      } catch (micError) {
        console.warn(
          'Could not access microphone. Recording only tab audio.',
          micError
        )
      }

      const composedStream = new MediaStream()
      destination.stream.getAudioTracks().forEach((track) => {
        composedStream.addTrack(track)
      })
      streamRef.current = composedStream
      setStream(composedStream)

      const options = { mimeType: 'audio/webm' }
      const mediaRecorder = new MediaRecorder(composedStream, options)
      mediaRecorderRef.current = mediaRecorder

      mediaRecorder.onstart = async () => {
        const recordingId = await addRecording(new Blob())
        form.setValue('recordingId', recordingId)
      }

      mediaRecorder.ondataavailable = async (event) => {
        if (event.data.size > 0) {
          mediaChunksRef.current.push(event.data)
          const recordingId = form.getValues('recordingId')
          if (recordingId && mediaChunksRef.current.length % 60 == 0) {
            const audioBlob = new Blob(mediaChunksRef.current, {
              type: 'audio/webm',
            })
            await updateRecording(recordingId, audioBlob)
          }
        }
      }

      mediaRecorder.onerror = () => {
        setError('Recording error occurred. Please try again.')
        stopAllTracks()
      }

      mediaRecorder.onstop = async () => {
        if (mediaChunksRef.current.length > 0) {
          const audioBlob = new Blob(mediaChunksRef.current, {
            type: 'audio/webm',
          })
          setRecordedAudio(audioBlob)
          const recordingId = form.getValues('recordingId')
          if (recordingId) {
            await updateRecording(recordingId, audioBlob)
          }
        } else {
          setError(
            'No audio data was recorded. Please try again and ensure audio is shared.'
          )
        }
        stopAllTracks()
      }

      await requestWakeLock()
      mediaRecorder.start(1000)
      setIsRecording(true)
    } catch (error) {
      setError(
        error instanceof Error ? error.message : 'An unknown error occurred'
      )
      setRecordingUIState('idle')
      stopAllTracks()
    } finally {
      isStartingRecordingRef.current = false
    }
  }, [
    addRecording,
    form,
    requestWakeLock,
    selectedDeviceId,
    setRecordedAudio,
    setRecordingUIState,
    stopAllTracks,
    updateRecording,
  ])

  const handleCountdownCancel = () => {
    stopAllTracks()
    setRecordingUIState('idle')
  }

  const {
    isStartingRecording,
    isPreparingRecording,
    startCountdown,
    handleLoadingComplete,
    handleLoadingCancel,
  } = useCountdown({
    onComplete: startRecording,
    onCancel: handleCountdownCancel,
  })

  async function handleStartRecording() {
    setError(null)
    setRecordedAudio(null)
    setRecordingUIState('starting')

    try {
      if (!navigator.mediaDevices?.getDisplayMedia) {
        throw new Error(
          'Screen capture is not supported in this browser. Please use Chrome or Edge.'
        )
      }

      const screenStream = await navigator.mediaDevices.getDisplayMedia({
        video: true,
        audio: true,
      })

      if (!screenStream.getAudioTracks().length) {
        screenStream.getTracks().forEach((track) => track.stop())
        throw new Error(
          "No audio track available from the tab. When sharing, please switch on 'Share audio' in the dialog."
        )
      }

      screenStreamRef.current = screenStream
      setStream(screenStream)
      startCountdown()
    } catch (error) {
      setRecordingUIState('idle')
      setError(
        error instanceof Error ? error.message : 'An unknown error occurred'
      )
    }
  }

  if (isStartingRecording || isPreparingRecording) {
    return (
      <RecordingLoading
        onComplete={handleLoadingComplete}
        onCancel={handleLoadingCancel}
      />
    )
  }

  if (!permissionGranted || !audioDevices.length) {
    return (
      <MicrophonePermission
        onPermissionGranted={handlePermissionGranted}
        onError={setError}
      />
    )
  }

  return (
    <div className="space-y-4">
      {recordedAudio ? (
        <div className="govuk-!-margin-top-4 space-y-3">
          <AudioPlayerComponent audioBlob={recordedAudio} />
          <div className="flex justify-end">
            <GovukButton
              type="button"
              onClick={() => setDiscardDialogOpen(true)}
              variant="secondary"
            >
              Discard Recording
            </GovukButton>
          </div>
        </div>
      ) : (
        <div className="flex flex-col space-y-4">
          {!isRecording ? (
            <>
              <GovukFormGroup>
                <GovukLabel htmlFor="virtual-microphone-select">
                  Choose microphone
                </GovukLabel>
                <select
                  className="govuk-select w-full"
                  id="virtual-microphone-select"
                  value={selectedDeviceId}
                  onChange={(e) => setSelectedDeviceId(e.target.value)}
                  disabled={isRecording}
                >
                  {audioDevices.map((device) => (
                    <option key={device.deviceId} value={device.deviceId}>
                      {device.label}
                    </option>
                  ))}
                </select>
              </GovukFormGroup>

              <div className="govuk-inset-text govuk-!-margin-top-0">
                <p className="govuk-body">
                  Open your virtual meeting in another tab, then start recording
                  below. When prompted to share, turn on &quot;Share
                  audio&quot;.
                </p>
                <p className="govuk-body">
                  On Windows, share your entire screen, as sharing a single
                  tab&apos;s audio is not supported. On Mac, you can share just
                  the meeting tab.
                </p>
                <GovukButton
                  type="button"
                  onClick={handleStartRecording}
                  className="govuk-!-margin-bottom-0"
                >
                  Start recording
                </GovukButton>
              </div>
            </>
          ) : (
            <div className="space-y-4">
              <RecordingControl
                stream={stream}
                isRecording={isRecording}
                onStopRecording={stopRecording}
                onPauseStateChange={handlePauseStateChange}
              />
            </div>
          )}
        </div>
      )}

      {err && (
        <p className="govuk-error-message" role="alert">
          <span className="govuk-visually-hidden">Error:</span> {err}
        </p>
      )}
      <DiscardConfirmDialog
        open={discardDialogOpen}
        setOpen={setDiscardDialogOpen}
        onClickConfirm={() => {
          setRecordedAudio(null)
          setDiscardDialogOpen(false)
          const recordingId = form.getValues('recordingId')
          if (recordingId) {
            removeRecording(recordingId)
          }
        }}
      />
    </div>
  )
}

export default TabRecorder
