'use client'

import { StartTranscriptionSection } from '@/components/audio/start-transcription-section'
import { GovukButton } from '@/components/govuk'
import { useStartTranscription } from '@/hooks/useStartTranscription'
import { cn } from '@/lib/utils'
import Dropzone from 'react-dropzone'
import { Controller, FormProvider } from 'react-hook-form'

export const AudioUploadForm = () => {
  const { isPending, onSubmit, form } = useStartTranscription()
  const file = form.watch('file')
  return (
    <FormProvider {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} noValidate>
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
