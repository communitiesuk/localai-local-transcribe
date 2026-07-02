'use client'

import { StartTranscriptionSection } from '@/components/audio/start-transcription-section'
import { GovukButton } from '@/components/govuk'
import { useStartTranscription } from '@/hooks/useStartTranscription'
import Dropzone from 'react-dropzone'
import { Controller, FormProvider } from 'react-hook-form'

export const AudioUploadForm = () => {
  const { isPending, onSubmit, form } = useStartTranscription()
  const file = form.watch('file')
  return (
    <FormProvider {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} noValidate>
        <p className="govuk-hint">Maximum file size: 5GB</p>
        <Controller
          control={form.control}
          name="file"
          render={({ field: { onChange } }) => (
            <Dropzone
              onDrop={(acceptedFiles) =>
                acceptedFiles.length && onChange(acceptedFiles[0])
              }
              accept={{
                'audio/*': [],
                'video/*': [],
              }}
              multiple={false}
            >
              {({ getRootProps, getInputProps }) => (
                <div
                  {...getRootProps()}
                  className="govuk-!-margin-bottom-4 cursor-pointer border border-[#b1b4b6]"
                >
                  <div className="govuk-body govuk-!-margin-bottom-0 bg-[#f3f2f1] px-3 py-2">
                    {file instanceof File ? file.name : 'No file chosen'}
                  </div>
                  <div className="govuk-body-s govuk-!-margin-bottom-0 px-3 py-2">
                    <span className="govuk-link">Choose file</span> or drop file
                  </div>
                  <input {...getInputProps()} />
                </div>
              )}
            </Dropzone>
          )}
        />
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
