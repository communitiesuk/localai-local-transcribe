'use client'

import { useRouter } from 'next/navigation'
import { useEffect, useRef, useState } from 'react'

import RecordingControl from './recording-control'
import { DiscardConfirmDialog } from '@/components/audio/discard-dialog'
import { GovukButton, GovukFormGroup, GovukLabel } from '@/components/govuk'
import { useStartTranscription } from '@/hooks/use-start-transcription'
import { Controller, FormProvider } from 'react-hook-form'
import { MicrophonePermission } from './microphone-permission'
import { RecordingLoading } from '@/components/recording-loading'
import { Loader2 } from 'lucide-react'
import AudioPlayerComponent from './audio-player'
import { useMicRecorder } from '@/hooks/use-mic-recorder'

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
          router.push(`/new/metadata/${transcriptionId}`)
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
  const {
    error,
    setError,
    audioDevices,
    selectedDeviceId,
    setSelectedDeviceId,
    permissionGranted,
    isDialogOpen,
    setIsDialogOpen,
    mediaRecorderStream,
    isRecording,
    recordingUIState,
    isStartingRecording,
    isPreparingRecording,
    handlePermissionGranted,
    handleStartRecordingClick,
    handleLoadingComplete,
    handleLoadingCancel,
    stopRecording,
    handlePauseStateChange,
    discardRecording,
  } = useMicRecorder({ recordedAudio, setRecordedAudio })

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
        onClickConfirm={discardRecording}
      />
    </div>
  )
}
