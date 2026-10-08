'use client'

import {
  GovukButton,
  GovukButtonGroup,
  GovukHeading,
  GovukRadios,
} from '@/components/govuk'
import { Minute, TranscriptionGetResponse } from '@/lib/client'
import {
  createMinuteTranscriptionTranscriptionIdMinutesPostMutation,
  listMinuteVersionsMinutesMinuteIdVersionsGetOptions,
  listMinutesForTranscriptionTranscriptionTranscriptionIdMinutesGetQueryKey,
} from '@/lib/client/@tanstack/react-query.gen'
import { recordAnalyticsEvent } from '@/lib/analytics'
import { ProcessingSpinner } from '@/components/processing-spinner'
import {
  isDefaultTemplateId,
  templateValue,
  userTemplateIdForRequest,
  useTemplates,
} from '@/hooks/use-templates'
import { useBannerStore } from '@/stores/use-banner-store'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { LoaderCircle } from 'lucide-react'
import posthog from 'posthog-js'
import { useEffect, useRef, useState } from 'react'
import { MinuteEditor } from '@/app/transcriptions/[transcriptionId]/MinuteTab/minute-editor/minute-editor'

enum DocumentGenerationState {
  Idle = 'idle',
  Creating = 'creating',
  Generating = 'generating',
  Finished = 'finished',
}

const terminalVersionStatuses = ['completed', 'failed']

const getGenerationState = ({
  createdMinuteId,
  isCreatePending,
  versionStatus,
}: {
  createdMinuteId: string | null
  isCreatePending: boolean
  versionStatus?: string
}): DocumentGenerationState => {
  if (versionStatus && terminalVersionStatuses.includes(versionStatus)) {
    return DocumentGenerationState.Finished
  }

  if (createdMinuteId !== null) {
    return DocumentGenerationState.Generating
  }

  if (isCreatePending) {
    return DocumentGenerationState.Creating
  }

  return DocumentGenerationState.Idle
}

export const NewDocumentTab = ({
  transcription,
  onCancel,
  onCreated,
  onMinuteCreated,
  onFailedResultRemoved,
  onActivityChange,
  onCitationClicked,
}: {
  transcription: TranscriptionGetResponse
  onCancel: () => void
  onCreated: (templateName: string) => void
  onMinuteCreated?: (minuteId: string) => void
  onFailedResultRemoved: () => void
  onActivityChange?: (busy: boolean) => void
  onCitationClicked?: (citationIndex: number) => void
}) => {
  const [selectedValue, setSelectedValue] = useState('')
  const [createdMinuteId, setCreatedMinuteId] = useState<string | null>(null)
  const [createdTemplateName, setCreatedTemplateName] = useState('')
  const renamedRef = useRef(false)

  const { setBanner } = useBannerStore()

  const { sortedTemplates, isLoading, isError, refetchTemplates } =
    useTemplates()

  const { data: versions = [] } = useQuery({
    ...listMinuteVersionsMinutesMinuteIdVersionsGetOptions({
      path: { minute_id: createdMinuteId ?? '' },
    }),
    enabled: createdMinuteId !== null,
    refetchInterval: (query) => {
      const status = query.state.data?.[0]?.status
      return status === 'awaiting_start' || status === 'in_progress'
        ? 1000
        : false
    },
  })
  const versionStatus = versions[0]?.status

  const queryClient = useQueryClient()
  const { mutate: createMinute, isPending } = useMutation({
    ...createMinuteTranscriptionTranscriptionIdMinutesPostMutation(),
  })

  const selectedTemplate = sortedTemplates.find(
    (t) => templateValue(t) === selectedValue
  )

  const generationState = getGenerationState({
    createdMinuteId,
    isCreatePending: isPending,
    versionStatus,
  })
  const isCompleted =
    createdMinuteId !== null &&
    generationState === DocumentGenerationState.Finished &&
    versionStatus === 'completed'

  useEffect(() => {
    if (isCompleted && !renamedRef.current) {
      renamedRef.current = true
      onCreated(createdTemplateName)
    }
  }, [isCompleted, createdTemplateName, onCreated])

  useEffect(() => {
    if (!isCompleted) {
      onActivityChange?.(generationState !== DocumentGenerationState.Finished)
    }
  }, [isCompleted, generationState, onActivityChange])

  if (
    generationState === DocumentGenerationState.Finished &&
    createdMinuteId !== null
  ) {
    const createdMinute: Minute = {
      id: createdMinuteId,
      transcription_id: transcription.id!,
      template_name: createdTemplateName,
    }

    return (
      <MinuteEditor
        transcription={transcription}
        minute={createdMinute}
        onActivityChange={onActivityChange}
        onCitationClicked={onCitationClicked}
        onRemoved={onFailedResultRemoved}
      />
    )
  }

  if (
    generationState === DocumentGenerationState.Creating ||
    generationState === DocumentGenerationState.Generating
  ) {
    return (
      <ProcessingSpinner
        label="Creating document"
        message={`Creating ‘${selectedTemplate?.name ?? createdTemplateName}’…`}
      />
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
          onClick={refetchTemplates}
        >
          Try again
        </GovukButton>
      </div>
    )
  }

  const handleCreate = () => {
    if (!selectedTemplate) return
    renamedRef.current = false
    setCreatedMinuteId(null)
    recordAnalyticsEvent('summary_requested')
    createMinute(
      {
        path: { transcription_id: transcription.id! },
        body: {
          template_name: selectedTemplate.name,
          template_id: userTemplateIdForRequest(selectedTemplate),
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
            style: isDefaultTemplateId(selectedTemplate.id)
              ? selectedTemplate.name
              : 'User generated',
          })
          setCreatedTemplateName(selectedTemplate.name)
          setCreatedMinuteId(data.minute_id)
          onMinuteCreated?.(data.minute_id)
        },
        onError: () => {
          setBanner({
            variant: 'important',
            title: 'There is a problem',
            message:
              'Something went wrong creating your document. Please try again.',
          })
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
          value: templateValue(template),
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
        <GovukButton variant="link" onClick={onCancel}>
          Cancel
        </GovukButton>
      </GovukButtonGroup>
    </div>
  )
}
