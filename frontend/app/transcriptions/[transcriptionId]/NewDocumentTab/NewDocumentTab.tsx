'use client'

import { MinuteEditor } from '@/app/transcriptions/[transcriptionId]/MinuteTab/minute-editor/minute-editor'
import {
  GovukButton,
  GovukButtonGroup,
  GovukHeading,
  GovukRadios,
} from '@/components/govuk'
import { TranscriptionGetResponse } from '@/lib/client'
import {
  createMinuteTranscriptionTranscriptionIdMinutesPostMutation,
  getUserTemplatesUserTemplatesGetOptions,
  listMinutesForTranscriptionTranscriptionTranscriptionIdMinutesGetOptions,
  listMinutesForTranscriptionTranscriptionTranscriptionIdMinutesGetQueryKey,
} from '@/lib/client/@tanstack/react-query.gen'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { LoaderCircle } from 'lucide-react'
import posthog from 'posthog-js'
import { useState } from 'react'

export const NewDocumentTab = ({
  transcription,
  onCancel,
  onCreated,
}: {
  transcription: TranscriptionGetResponse
  onCancel: () => void
  onCreated: (templateName: string) => void
}) => {
  const [selectedValue, setSelectedValue] = useState('')
  const [createdMinuteId, setCreatedMinuteId] = useState<string | null>(null)

  const {
    data: templates = [],
    isLoading,
    isError,
    refetch,
  } = useQuery(getUserTemplatesUserTemplatesGetOptions())

  const { data: minutes = [] } = useQuery({
    ...listMinutesForTranscriptionTranscriptionTranscriptionIdMinutesGetOptions(
      {
        path: { transcription_id: transcription.id! },
      }
    ),
    enabled: createdMinuteId !== null,
  })

  const queryClient = useQueryClient()
  const { mutate: createMinute, isPending } = useMutation({
    ...createMinuteTranscriptionTranscriptionIdMinutesPostMutation(),
  })

  const selectedTemplate = templates.find(
    (t) => (t.id ?? t.name) === selectedValue
  )

  if (createdMinuteId) {
    const createdMinute = minutes.find((m) => m.id === createdMinuteId)
    if (!createdMinute) {
      return (
        <div className="flex items-center justify-center py-8">
          <LoaderCircle className="animate-spin" aria-hidden="true" />
        </div>
      )
    }
    return <MinuteEditor transcription={transcription} minute={createdMinute} />
  }

  if (isPending) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-16">
        <LoaderCircle size={64} className="animate-spin" aria-hidden="true" />
        <p className="govuk-body" role="status">
          Creating ‘{selectedTemplate?.name}’…
        </p>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <LoaderCircle className="animate-spin" aria-hidden="true" />
      </div>
    )
  }

  if (isError) {
    return (
      <div>
        <p className="govuk-body">
          Something went wrong fetching your templates.
        </p>
        <GovukButton
          type="button"
          variant="secondary"
          onClick={() => refetch()}
        >
          Try again
        </GovukButton>
      </div>
    )
  }

  const sortedTemplates = [...templates].sort((a, b) =>
    a.name.localeCompare(b.name)
  )

  const handleCreate = () => {
    if (!selectedTemplate) return
    createMinute(
      {
        path: { transcription_id: transcription.id! },
        body: {
          template_name: selectedTemplate.name,
          template_id: selectedTemplate.id,
        },
      },
      {
        onSuccess: (data) => {
          queryClient.invalidateQueries({
            queryKey:
              listMinutesForTranscriptionTranscriptionTranscriptionIdMinutesGetQueryKey(
                { path: { transcription_id: transcription.id! } }
              ),
          })
          posthog.capture('generate_ai_minutes_started', {
            style: selectedTemplate.id
              ? 'User generated'
              : selectedTemplate.name,
          })
          setCreatedMinuteId(data.minute_id)
          onCreated(selectedTemplate.name)
        },
      }
    )
  }

  return (
    <div>
      <GovukHeading as="h2" size="m">
        Choose a document template
      </GovukHeading>
      <p className="govuk-body govuk-hint">
        Choose a template style for your conversation
      </p>
      <GovukRadios
        name="document-template"
        value={selectedValue}
        onChange={setSelectedValue}
        options={sortedTemplates.map((template) => ({
          label: template.name,
          value: template.id ?? template.name,
          hint: template.description,
        }))}
      />
      <GovukButtonGroup className="govuk-!-margin-top-4">
        <GovukButton
          type="button"
          variant="secondary"
          disabled={!selectedValue}
          onClick={handleCreate}
        >
          Create
        </GovukButton>
        <button
          type="button"
          className="govuk-link cursor-pointer border-0 bg-transparent p-0"
          onClick={onCancel}
        >
          Cancel
        </button>
      </GovukButtonGroup>
    </div>
  )
}
