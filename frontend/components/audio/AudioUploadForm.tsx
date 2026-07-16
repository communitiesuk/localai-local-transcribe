'use client'

import { StartTranscriptionSection } from '@/components/audio/start-transcription-section'
import { GovukButton, GovukFormGroup } from '@/components/govuk'
import { useStartTranscription } from '@/hooks/useStartTranscription'
import {
  MAX_UPLOAD_FILE_SIZE_BYTES,
  MAX_UPLOAD_FILE_SIZE_LABEL,
} from '@/lib/constants'
import { cn } from '@/lib/utils'
import { useState } from 'react'
import Dropzone, { type FileRejection } from 'react-dropzone'
import { Controller, FormProvider } from 'react-hook-form'

export const AudioUploadForm = () => {
  const { isPending, onSubmit, form } = useStartTranscription()
  const file = form.watch('file')
  const [fileError, setFileError] = useState<string | null>(null)

  const handleDropRejected = (rejections: FileRejection[]) => {
    const isTooLarge = rejections.some((rejection) =>
      rejection.errors.some((error) => error.code === 'file-too-large')
    )
    setFileError(
      isTooLarge
        ? `The selected file must be smaller than ${MAX_UPLOAD_FILE_SIZE_LABEL}`
        : 'The selected file must be an audio or video file'
    )
  }

  return (
    <FormProvider {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} noValidate>
        <GovukFormGroup hasError={!!fileError}>
          <p className="govuk-hint">
            Maximum file size: {MAX_UPLOAD_FILE_SIZE_LABEL}
          </p>
          {fileError && (
            <p className="govuk-error-message" role="alert">
              <span className="govuk-visually-hidden">Error:</span> {fileError}
            </p>
          )}
          <Controller
            control={form.control}
            name="file"
            render={({ field: { onChange } }) => (
              <Dropzone
                onDrop={(acceptedFiles) => {
                  if (acceptedFiles.length) {
                    setFileError(null)
                    onChange(acceptedFiles[0])
                  }
                }}
                onDropRejected={handleDropRejected}
                accept={{
                  'audio/*': [],
                  'video/*': [],
                }}
                maxSize={MAX_UPLOAD_FILE_SIZE_BYTES}
                multiple={false}
              >
                {({ getRootProps, getInputProps }) => (
                  <div
                    {...getRootProps()}
                    className={cn(
                      'govuk-!-margin-bottom-4 cursor-pointer border-2 border-[var(--govuk-border-colour)] p-6',
                      file instanceof File
                        ? 'border-solid bg-[#f3f2f1]'
                        : 'border-dashed'
                    )}
                  >
                    <div
                      className={cn(
                        'govuk-body govuk-!-margin-bottom-3 px-4 py-3',
                        file instanceof File ? 'bg-white' : 'bg-[#bbd4ea]'
                      )}
                    >
                      {file instanceof File ? file.name : 'No file chosen'}
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="govuk-button govuk-button--secondary govuk-!-margin-bottom-0">
                        Choose file
                      </span>
                      <span className="govuk-body govuk-!-margin-bottom-0">
                        or drop file
                      </span>
                    </div>
                    <input {...getInputProps()} />
                  </div>
                )}
              </Dropzone>
            )}
          />
        </GovukFormGroup>
        <StartTranscriptionSection isShowing={!!file} isPending={isPending} />
        {!file && (
          <GovukButton type="submit" disabled>
            Continue
          </GovukButton>
        )}
      </form>
    </FormProvider>
  )
}
