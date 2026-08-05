import { GovukButton } from '@/components/govuk'
import { useUpdateTranscription } from '@/hooks/use-update-transcription-speakers'
import { JobStatus } from '@/lib/client'
import { cn } from '@/lib/utils'
import posthog from 'posthog-js'
import { useCallback, useEffect, useState } from 'react'
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
  const { updateTitle } = useUpdateTranscription(transcriptionId)
  const form = useForm<{ title: string }>({
    defaultValues: { title: '' },
    values: { title: title || '' },
    mode: 'onBlur',
  })
  const titleValue = useWatch({ name: 'title', control: form.control })
  const onSubmit = useCallback(
    async ({ title }: { title: string }) => {
      await updateTitle(title)
      posthog.capture('edited_transcript_title', {
        transcriptionId: transcriptionId,
      })
      setEditing(false)
    },
    [transcriptionId, updateTitle]
  )
  useEffect(() => {
    if (editing) {
      form.setFocus('title', { shouldSelect: true })
    }
  }, [editing, form])

  const placeholder = ['awaiting_start', 'in_progress'].includes(status)
    ? 'Generating title'
    : 'Add title'

  if (editing) {
    return (
      <input
        {...form.register('title', {
          onBlur: () => {
            void form.handleSubmit(onSubmit)()
          },
        })}
        className="govuk-input govuk-!-font-size-36 govuk-!-font-weight-bold govuk-!-margin-bottom-2"
        placeholder={placeholder}
        onKeyDown={(e) => {
          if (e.key === 'Enter') {
            void form.handleSubmit(onSubmit)()
          }
        }}
      />
    )
  }

  return (
    <div className="flex items-baseline gap-2">
      <h1
        className={cn('govuk-heading-l govuk-!-margin-bottom-2', {
          'text-[var(--govuk-secondary-text-colour)]': !title,
        })}
      >
        {titleValue || placeholder}
      </h1>
      <GovukButton
        type="button"
        variant="secondary"
        className="govuk-!-margin-bottom-0"
        onClick={() => {
          setEditing(true)
        }}
      >
        Rename
      </GovukButton>
    </div>
  )
}
