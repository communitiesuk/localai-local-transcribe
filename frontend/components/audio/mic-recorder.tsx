'use client'

import { useRouter } from 'next/navigation'
import { useCallback, useEffect, useRef, useState } from 'react'

import RecordingControl from './recording-control'
import { DiscardConfirmDialog } from '@/components/audio/discard-dialog'
import { GovukButton, GovukFormGroup, GovukLabel } from '@/components/govuk'
import { useTabCloseWarning } from '@/hooks/use-tab-close-warning'
import { useWakeLock } from '@/hooks/use-wake-lock'
import {
  useStartTranscription,
  type TranscriptionForm,
} from '@/hooks/use-start-transcription'
import { useRecordingDb } from '@/providers/transcription-db-provider'
import { Controller, FormProvider, useFormContext } from 'react-hook-form'
import { AudioDevice, MicrophonePermission } from './microphone-permission'
import { useRecordingUIStore } from '@/stores/use-recording-ui-store'
import { RecordingLoading } from '@/components/recording-loading'
import { useCountdown } from '@/hooks/use-countdown'
import { Loader2 } from 'lucide-react'
import AudioPlayerComponent from './audio-player'

export function MicRecorderForm() {
  const router = useRouter()
  const { isPending, onSubmit, form } = useStartTranscription()
  const watchBlob = form.watch('file')
  const submittedBlobRef = useRef<Blob | File | null>(null)
  const [isProcessingRecording, setIsProcessingRecording] = useState(false)

  useEffect(() => {
    if (!watchBlob || submittedBlobRef.current === watchBlob) {
      return
    }

    submittedBlobRef.current = watchBlob
    setIsProcessingRecording(true)

    void form
      .handleSubmit(async (formValues) => {
        const transcriptionId = await onSubmit(formValues)
        if (transcriptionId) {
          router.push(`/transcriptions/${transcriptionId}?details=open`)
        }
      })()
      .finally(() => {
        setIsProcessingRecording(false)
      })
  }, [form, onSubmit, router, watchBlob])

  return (
    <FormProvider {...form}>
      <form>
        {isProcessingRecording || isPending ? (
          <div className="flex h-72 flex-col items-center justify-center gap-4">
            <Loader2 size={80} className="animate-spin" aria-hidden="true" />
            <p className="govuk-body">Processing recording...</p>
          </div>
        ) : (
          <Controller
            name="file"
            control={form.control}
            render={({ field: { value, onChange } }) => (
              <MicRecorderComponent
                recordedAudio={value}
                setRecordedAudio={onChange}
              />
            )}
          />
        )}
      </form>
    </FormProvider>
  )
}

function MicRecorderComponent({
  recordedAudio,
  setRecordedAudio,
}: {
  recordedAudio: Blob | null
  setRecordedAudio: (blob: Blob | null) => void
}) {
  const { releaseWakeLock, requestWakeLock } = useWakeLock()
  const [error, setError] = useState<string | null>(null)
  const [audioDevices, setAudioDevices] = useState<AudioDevice[]>([])
  const [selectedDeviceId, setSelectedDeviceId] = useState<string>('')
  const [permissionGranted, setPermissionGranted] = useState<boolean>(false)
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const form = useFormContext<TranscriptionForm>()
  const { removeRecording, addRecording, updateRecording } = useRecordingDb()
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const [mediaRecorderStream, setMediaRecorderStream] =
    useState<MediaStream | null>(null)
  const micStreamRef = useRef<MediaStream | null>(null)
  const mediaChunksRef = useRef<Blob[]>([])
  const isStartingRecordingRef = useRef(false)
  const [isRecording, setIsRecording] = useState(false)
  const { recordingUIState, setRecordingUIState } = useRecordingUIStore()

  const stopAllTracks = useCallback(() => {
    isStartingRecordingRef.current = false

    if (micStreamRef.current) {
      micStreamRef.current.getTracks().forEach((track) => track.stop())
    }
    micStreamRef.current = null
    mediaRecorderRef.current = null
    setMediaRecorderStream(null)

    setIsRecording(false)
    releaseWakeLock()
  }, [releaseWakeLock])

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

    try {
      setError(null)
      mediaChunksRef.current = []
      const micStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          deviceId: selectedDeviceId,
          noiseSuppression: false,
          echoCancellation: false,
        },
      })
      micStreamRef.current = micStream
      const options = { mimeType: 'audio/webm' }
      const mediaRecorder = new MediaRecorder(micStream, options)
      mediaRecorderRef.current = mediaRecorder
      setMediaRecorderStream(mediaRecorder.stream)

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
        setRecordingUIState('idle')
        // Don't call stopRecording here as it might cause a loop
        // Just clean up manually if needed
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
          setRecordingUIState('idle')
        }
        stopAllTracks()
      }

      // Start recording
      setRecordedAudio(null)
      await requestWakeLock()
      mediaRecorder.start(1000) // Collect data every second
      setIsRecording(true)
    } catch (micError) {
      console.warn('Error occurred starting audio recording.', micError)
      setError('Error occurred starting audio recording. Please try again.')
      setRecordingUIState('idle')
      stopAllTracks()
    } finally {
      isStartingRecordingRef.current = false
    }
    // Create a media recorder from the composed stream
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

  const stopRecording = useCallback(() => {
    // Prevent multiple calls to stopRecording
    if (!mediaRecorderRef.current || !isRecording) {
      return
    }
    try {
      // Only call stop() if the state is not 'inactive'
      if (mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop()
      } else {
        stopAllTracks()
      }
    } catch {
      // Clean up streams even if stop fails
      stopAllTracks()
    }
  }, [isRecording, stopAllTracks])

  useEffect(() => {
    return () => {
      stopRecording()
    }
  }, [stopRecording])

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

  const handlePermissionGranted = (devices: AudioDevice[]) => {
    setAudioDevices(devices)
    setSelectedDeviceId(devices[0].deviceId)
    setPermissionGranted(true)
    setError(null)
  }

  useTabCloseWarning(!!recordedAudio || isRecording)

  const handleCountdownCancel = () => {
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

  const handleStartRecordingClick = () => {
    setError(null)
    setRecordedAudio(null)
    setRecordingUIState('starting')
    startCountdown()
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
      <div className="space-y-4">
        <MicrophonePermission
          onPermissionGranted={handlePermissionGranted}
          onError={setError}
        />
        {error && (
          <p className="govuk-error-message" role="alert">
            <span className="govuk-visually-hidden">Error:</span> {error}
          </p>
        )}
      </div>
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
              onClick={() => setIsDialogOpen(true)}
              variant="secondary"
            >
              Discard Recording
            </GovukButton>
          </div>
        </div>
      ) : !isRecording && recordingUIState !== 'stopping' ? (
        <div className="flex flex-col space-y-4">
          <GovukFormGroup>
            <GovukLabel htmlFor="microphone-select">
              Choose microphone
            </GovukLabel>
            <select
              className="govuk-select w-full"
              id="microphone-select"
              value={selectedDeviceId}
              onChange={(e) => setSelectedDeviceId(e.target.value)}
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
              This records audio from your microphone, so only in-person
              meetings or calls played out loud will be picked up. Check that
              sound waves appear once you start.
            </p>
            <GovukButton
              type="button"
              onClick={handleStartRecordingClick}
              className="govuk-!-margin-bottom-0"
            >
              Start recording
            </GovukButton>
          </div>
        </div>
      ) : (
        <div className="flex flex-col space-y-2">
          <RecordingControl
            stream={mediaRecorderStream}
            isRecording={isRecording}
            onStopRecording={stopRecording}
            onPauseStateChange={handlePauseStateChange}
          />
        </div>
      )}

      {error && (
        <p className="govuk-error-message" role="alert">
          <span className="govuk-visually-hidden">Error:</span> {error}
        </p>
      )}

      <DiscardConfirmDialog
        open={isDialogOpen}
        setOpen={setIsDialogOpen}
        onClickConfirm={() => {
          setRecordedAudio(null)
          setIsDialogOpen(false)
          const recordingId = form.getValues('recordingId')
          if (recordingId) {
            removeRecording(recordingId)
          }
        }}
      />
    </div>
  )
}
