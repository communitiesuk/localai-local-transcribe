'use client'

import { useEffect, useRef } from 'react'

import { GovukButton, GovukFormGroup, GovukLabel } from '@/components/govuk'
import RecordingControl from './recording-control'
import { UploadStatus } from '@/components/audio/upload-status'
import { useStartTranscription } from '@/hooks/use-start-transcription'
import { Controller, FormProvider } from 'react-hook-form'
import { MicrophonePermission } from './microphone-permission'
import { RecordingLoading } from '@/components/recording-loading'
import { useMicRecorder } from '@/hooks/use-mic-recorder'
import { useUploadRecordingStore } from '@/stores/use-upload-recording-store'

export function MicRecorderForm() {
  const { onSubmit, form } = useStartTranscription()

  const startUpload = useUploadRecordingStore((store) => store.startUpload)
  const uploadStatus = useUploadRecordingStore((store) => store.status)

  const watchBlob = form.watch('file')
  const submittedBlobRef = useRef<Blob | File | null>(null)

  useEffect(() => {
    if (!watchBlob || submittedBlobRef.current === watchBlob) {
      return
    }
    submittedBlobRef.current = watchBlob

    void form.handleSubmit((formValues) => {
      startUpload('recording', formValues, onSubmit)
    })()
  }, [form, onSubmit, startUpload, watchBlob])

  if (uploadStatus !== 'idle') {
    return <UploadStatus />
  }

  return (
    <FormProvider {...form}>
      <form>
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
      {!isRecording && recordingUIState !== 'stopping' ? (
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
    </div>
  )
}
