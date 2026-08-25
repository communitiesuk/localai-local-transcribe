'use client'

import {
  GovukButton,
  GovukButtonGroup,
  GovukHeading,
  GovukRadios,
} from '@/components/govuk'
import {
  createMinuteTranscriptionTranscriptionIdMinutesPostMutation,
  getUserTemplatesUserTemplatesGetOptions,
  listMinutesForTranscriptionTranscriptionTranscriptionIdMinutesGetQueryKey,
} from '@/lib/client/@tanstack/react-query.gen'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { LoaderCircle } from 'lucide-react'
import posthog from 'posthog-js'
import { useState } from 'react'

export const NewDocumentTab = ({
  transcriptionId,
  onCancel,
  onCreated,
}: {
  transcriptionId: string
  onCancel: () => void
  onCreated: () => void
}) => {
  const {
    data: templates = [],
    isLoading,
    isError,
    refetch,
  } = useQuery(getUserTemplatesUserTemplatesGetOptions())

  const [selectedValue, setSelectedValue] = useState('')

  const queryClient = useQueryClient()
  const { mutate: createMinute, isPending } = useMutation({
    ...createMinuteTranscriptionTranscriptionIdMinutesPostMutation(),
  })

  const sortedTemplates = [...templates].sort((a, b) =>
    a.name.localeCompare(b.name)
  )
  const selectedTemplate = templates.find(
    (t) => (t.id ?? t.name) === selectedValue
  )

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

  const handleCreate = () => {
    if (!selectedTemplate) return
    createMinute(
      {
        path: { transcription_id: transcriptionId },
        body: {
          template_name: selectedTemplate.name,
          template_id: selectedTemplate.id,
        },
      },
      {
        onSuccess: () => {
          queryClient.invalidateQueries({
            queryKey:
              listMinutesForTranscriptionTranscriptionTranscriptionIdMinutesGetQueryKey(
                { path: { transcription_id: transcriptionId } }
              ),
          })
          posthog.capture('generate_ai_minutes_started', {
            style: selectedTemplate.id
              ? 'User generated'
              : selectedTemplate.name,
          })
          onCreated()
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
