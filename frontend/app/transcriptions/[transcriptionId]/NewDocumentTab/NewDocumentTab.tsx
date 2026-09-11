'use client'

import {
  GovukButton,
  GovukButtonGroup,
  GovukHeading,
  GovukRadios,
} from '@/components/govuk'
import { TranscriptionGetResponse } from '@/lib/client'
import {
  createMinuteTranscriptionTranscriptionIdMinutesPostMutation,
  getTemplatesTemplatesGetOptions,
  getUserTemplatesUserTemplatesGetOptions,
  listMinuteVersionsMinutesMinuteIdVersionsGetOptions,
  listMinutesForTranscriptionTranscriptionTranscriptionIdMinutesGetQueryKey,
  getMinuteMinutesMinutesIdGetOptions,
} from '@/lib/client/@tanstack/react-query.gen'
import { ProcessingSpinner } from '@/components/processing-spinner'
import { useBannerStore } from '@/stores/use-banner-store'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { LoaderCircle } from 'lucide-react'
import posthog from 'posthog-js'
import { useEffect, useRef, useState } from 'react'
import { MinuteEditor } from '@/app/transcriptions/[transcriptionId]/MinuteTab/minute-editor/minute-editor'

const templateValue = (template: { id: string | null; name: string }) =>
  template.id ?? `DEFAULT::${template.name}`

export const NewDocumentTab = ({
  transcription,
  onCancel,
  onCreated,
  onMinuteCreated,
  onActivityChange,
}: {
  transcription: TranscriptionGetResponse
  onCancel: () => void
  onCreated: (templateName: string) => void
  onMinuteCreated?: (minuteId: string) => void
  onActivityChange?: (busy: boolean) => void
}) => {
  const [selectedValue, setSelectedValue] = useState('')
  const [createdMinuteId, setCreatedMinuteId] = useState<string | null>(null)
  const [createdTemplateName, setCreatedTemplateName] = useState('')
  const renamedRef = useRef(false)

  const { setBanner } = useBannerStore()

  const {
    data: defaultTemplates = [],
    isLoading: isLoadingDefaultTemplates,
    isError: isDefaultTemplatesError,
    refetch: refetchDefaultTemplates,
  } = useQuery(getTemplatesTemplatesGetOptions())

  const {
    data: templates = [],
    isLoading,
    isError,
    refetch,
  } = useQuery(getUserTemplatesUserTemplatesGetOptions())

  const allTemplates = [
    ...defaultTemplates.map((template) => ({ ...template, id: null })),
    ...templates,
  ]

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

  const { data: minute = null } = useQuery({
    ...getMinuteMinutesMinutesIdGetOptions({
      path: { minutes_id: createdMinuteId ?? '' },
    }),
    enabled: createdMinuteId !== null,
  })

  const queryClient = useQueryClient()
  const { mutate: createMinute, isPending } = useMutation({
    ...createMinuteTranscriptionTranscriptionIdMinutesPostMutation(),
  })

  const selectedTemplate = allTemplates.find(
    (t) => templateValue(t) === selectedValue
  )

  const isCompleted =
    createdMinuteId !== null && versionStatus === 'completed' && minute
  const isFailed = createdMinuteId !== null && versionStatus === 'failed'
  const isCreating =
    !isFailed && (isPending || (createdMinuteId !== null && !isCompleted))

  useEffect(() => {
    if (isCompleted && !renamedRef.current) {
      renamedRef.current = true
      onCreated(createdTemplateName)
    } else if (isFailed) {
      setBanner({
        variant: 'important',
        title: 'There is a problem',
        message:
          'Something went wrong generating your document. Please try again.',
      })
    }
  }, [isCompleted, isFailed, createdTemplateName, onCreated, setBanner])

  useEffect(() => {
    if (!isCompleted) onActivityChange?.(!isFailed)
  }, [isCompleted, isFailed, onActivityChange])

  if (isCompleted) {
    return (
      <MinuteEditor
        transcription={transcription}
        minute={minute}
        onActivityChange={onActivityChange}
      />
    )
  }

  if (isCreating) {
    return (
      <ProcessingSpinner
        label="Creating document"
        message={`Creating ‘${selectedTemplate?.name ?? createdTemplateName}’…`}
      />
    )
  }

  if (isLoading || isLoadingDefaultTemplates) {
    return (
      <div className="flex items-center justify-center py-8">
        <LoaderCircle className="animate-spin" aria-hidden="true" />
      </div>
    )
  }

  if (isError || isDefaultTemplatesError) {
    return (
      <div>
        <p className="govuk-body">
          Something went wrong fetching your templates.
        </p>
        <GovukButton
          type="button"
          variant="secondary"
          onClick={() => {
            refetchDefaultTemplates()
            refetch()
          }}
        >
          Try again
        </GovukButton>
      </div>
    )
  }

  const sortedTemplates = [...allTemplates].sort((a, b) =>
    a.name.localeCompare(b.name)
  )

  const handleCreate = () => {
    if (!selectedTemplate) return
    renamedRef.current = false
    setCreatedMinuteId(null)
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
