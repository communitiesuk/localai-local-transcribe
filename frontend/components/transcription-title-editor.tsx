import {
  GovukButton,
  GovukButtonGroup,
  GovukErrorSummary,
} from '@/components/govuk'
import { useUpdateTranscription } from '@/hooks/use-update-transcription-speakers'
import { JobStatus } from '@/lib/client'
import { cn } from '@/lib/utils'
import posthog from 'posthog-js'
import { useCallback, useEffect, useRef, useState } from 'react'
import { useForm, useWatch } from 'react-hook-form'

export const TranscriptionTitleEditor = ({
  transcriptionId,
  title,
  status,
}: {
  transcriptionId: string
  title: string | null
  status: JobStatus
}) => {
  const [editing, setEditing] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const { updateTitle } = useUpdateTranscription(transcriptionId)
  const form = useForm<{ title: string }>({
    defaultValues: { title: '' },
    values: { title: title || '' },
  })
  const titleValue = useWatch({ name: 'title', control: form.control })
  const errorSummaryRef = useRef<HTMLDivElement>(null)
  const onSubmit = useCallback(
    async ({ title }: { title: string }) => {
      setErrorMessage(null)
      try {
        await updateTitle(title)
        posthog.capture('edited_transcript_title', {
          transcriptionId: transcriptionId,
        })
        setEditing(false)
      } catch {
        setErrorMessage(
          'We could not save the title. Your changes have not been lost, please try again.'
        )
      }
    },
    [transcriptionId, updateTitle]
  )
  const handleCancel = useCallback(() => {
    form.reset({ title: title || '' })
    setErrorMessage(null)
    setEditing(false)
  }, [form, title])
  useEffect(() => {
    if (editing) {
      form.setFocus('title', { shouldSelect: true })
    }
  }, [editing, form])
  useEffect(() => {
    if (errorMessage) errorSummaryRef.current?.focus()
  }, [errorMessage])

  const placeholder = ['awaiting_start', 'in_progress'].includes(status)
    ? 'Generating title'
    : 'Add title'

  const isSaving = form.formState.isSubmitting

  if (editing) {
    return (
      <div className="govuk-!-margin-bottom-4">
        {errorMessage && (
          <GovukErrorSummary
            ref={errorSummaryRef}
            tabIndex={-1}
            errorList={[{ href: '#transcription-title', text: errorMessage }]}
          />
        )}
        <input
          {...form.register('title')}
          id="transcription-title"
          className="govuk-input govuk-!-font-size-36 govuk-!-font-weight-bold govuk-!-margin-bottom-2 h-14"
          placeholder={placeholder}
          disabled={isSaving}
        />
        <GovukButtonGroup>
          <GovukButton
            type="button"
            onClick={() => void form.handleSubmit(onSubmit)()}
            disabled={isSaving}
          >
            Save
          </GovukButton>
          <GovukButton
            type="button"
            variant="secondary"
            onClick={handleCancel}
            disabled={isSaving}
          >
            Cancel
          </GovukButton>
        </GovukButtonGroup>
      </div>
    )
  }

  return (
    <div className="flex items-baseline gap-2">
      <h1
        className={cn(
          'govuk-heading-l govuk-!-margin-bottom-2 min-w-0 break-words',
          {
            'text-[var(--govuk-secondary-text-colour)]': !title,
          }
        )}
      >
        {titleValue || placeholder}
      </h1>
      <GovukButton
        type="button"
        variant="secondary"
        className="govuk-!-margin-bottom-0 shrink-0"
        onClick={() => {
          setEditing(true)
        }}
      >
        Rename
      </GovukButton>
    </div>
  )
}
