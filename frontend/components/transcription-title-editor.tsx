import { Button } from '@/components/ui/button'
import { useUpdateTranscription } from '@/hooks/use-update-transcription-speakers'
import { JobStatus } from '@/lib/client'
import { cn } from '@/lib/utils'
import { Edit } from 'lucide-react'
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
      await updateTitle(title || null)
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
        className="rounded-md border-2 border-slate-400 text-3xl font-bold"
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
      <h1 className={cn('text-3xl font-bold', { 'text-gray-400': !title })}>
        {titleValue || placeholder}
      </h1>
      <Button
        onClick={() => {
          setEditing(true)
        }}
        variant="ghost"
        className="text-slate-500"
      >
        <Edit /> Rename
      </Button>
    </div>
  )
}
