'use client'

import SimpleEditor from '@/app/transcriptions/[transcriptionId]/MinuteTab/components/editor/tiptap-editor'
import { GuardrailResponseComponent } from '@/app/transcriptions/[transcriptionId]/MinuteTab/components/editor/guardrail-response-component'
import { MinuteVersionSelect } from '@/app/transcriptions/[transcriptionId]/MinuteTab/minute-editor/minute-version-select'
import { NewMinuteDialog } from '@/app/transcriptions/[transcriptionId]/MinuteTab/NewMinuteDialog'
import { citationRegex, citationRegexWithSpace } from '@/lib/citationRegex'
import {
  Minute,
  MinuteVersionResponse,
  TranscriptionGetResponse,
} from '@/lib/client'
import {
  createMinuteVersionMinutesMinuteIdVersionsPostMutation,
  deleteMinuteVersionMinuteVersionsMinuteVersionIdDeleteMutation,
  listMinuteVersionsMinutesMinuteIdVersionsGetOptions,
  listMinuteVersionsMinutesMinuteIdVersionsGetQueryKey,
} from '@/lib/client/@tanstack/react-query.gen'
import convertAIMinutesToWordDoc from '@/lib/download-word-doc'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { FilePenLine, Loader2, LoaderCircle } from 'lucide-react'
import posthog from 'posthog-js'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Controller, useForm, useWatch } from 'react-hook-form'
import {
  GovukButton,
  GovukButtonGroup,
  GovukNotificationBanner,
} from '@/components/govuk'
import { AiEditPopover } from '@/app/transcriptions/[transcriptionId]/MinuteTab/minute-editor/ai-edit-popover'
import CopyButton from '@/components/ui/copy-button'
import { useBannerStore } from '@/stores/use-banner-store'

type MinuteEditorForm = {
  html: string
}

export function MinuteEditor({
  transcription,
  minute,
}: {
  transcription: TranscriptionGetResponse
  minute: Minute
}) {
  const [version, setVersion] = useState<string | undefined>(undefined)
  const [hideCitations, setHideCitations] = useState(false)
  const {
    data: minuteVersions = [],
    isLoading,
    isError: isErrorFetchingVersions,
    refetch,
  } = useQuery({
    ...listMinuteVersionsMinutesMinuteIdVersionsGetOptions({
      path: { minute_id: minute.id! },
    }),
    refetchInterval: (query) => {
      const data = query.state.data
      if (!data || data.length === 0) return false
      const currentVersion = data.find((v) => v.id === version) ?? data[0]
      return ['awaiting_start', 'in_progress'].includes(currentVersion.status)
        ? 1000
        : false
    },
  })

  const minuteVersion =
    minuteVersions.length > 0
      ? (minuteVersions.find((v) => v.id === version) ?? minuteVersions[0])
      : undefined

  const [editSourceVersionId, setEditSourceVersionId] = useState<
    string | undefined
  >(undefined)

  const fallbackAfterFailure =
    version === undefined && minuteVersion?.status === 'failed'
      ? (minuteVersions.find((v) => v.id === editSourceVersionId) ??
        minuteVersions[
          minuteVersions.findIndex((v) => v.id === minuteVersion.id) + 1
        ])
      : undefined

  const displayedMinuteVersion = fallbackAfterFailure ?? minuteVersion

  const isGenerating = useMemo(
    () =>
      ['awaiting_start', 'in_progress'].includes(
        displayedMinuteVersion?.status || ''
      ),
    [displayedMinuteVersion?.status]
  )
  const isError = useMemo(
    () => displayedMinuteVersion?.status == 'failed',
    [displayedMinuteVersion?.status]
  )

  const { setBanner } = useBannerStore()
  const previousVersionRef = useRef<{ id: string; status: string } | null>(null)
  useEffect(() => {
    if (minuteVersion) {
      const previous = previousVersionRef?.current
      const justCompletedAiEdit =
        previous?.id === minuteVersion.id &&
        previous?.status !== 'completed' &&
        minuteVersion?.status === 'completed' &&
        minuteVersion?.content_source === 'ai_edit'
      if (justCompletedAiEdit) {
        setBanner({
          variant: 'success',
          title: 'Success',
          message: `AI edits applied to ‘${minute.template_name}’.`,
        })
      }

      const justFailed =
        previous?.id === minuteVersion.id &&
        previous?.status !== 'failed' &&
        minuteVersion.status === 'failed'
      if (justFailed) {
        setBanner({
          variant: 'important',
          title: 'There is a problem',
          message:
            'Something went wrong creating your AI Edit. Please try again.',
        })
      }

      previousVersionRef.current = {
        id: minuteVersion.id,
        status: minuteVersion.status,
      }
    }
  }, [minuteVersion, minute.template_name, setBanner])

  const queryClient = useQueryClient()
  const [isEditable, setIsEditable] = useState(false)
  const form = useForm<MinuteEditorForm>()
  useEffect(() => {
    if (displayedMinuteVersion) {
      form.setValue('html', displayedMinuteVersion.html_content)
    }
  }, [form, displayedMinuteVersion])
  const htmlContent = useWatch({ name: 'html', control: form.control })
  const contentToCopy = useMemo(() => {
    return htmlContent?.replaceAll(citationRegexWithSpace, '') || ''
  }, [htmlContent])
  const hasCitations = useMemo(() => {
    return !!htmlContent?.match(citationRegex)
  }, [htmlContent])
  useEffect(() => {}, [htmlContent])
  const { mutate: saveEdit } = useMutation({
    ...createMinuteVersionMinutesMinuteIdVersionsPostMutation(),
  })

  const onSuccess = useCallback(() => {
    setIsEditable(false)
    setVersion(undefined)
    queryClient.invalidateQueries({
      queryKey: listMinuteVersionsMinutesMinuteIdVersionsGetQueryKey({
        path: { minute_id: minute.id! },
      }),
    })
  }, [minute.id, queryClient])

  const onSubmit = useCallback(
    (data: MinuteEditorForm) => {
      if (data.html != displayedMinuteVersion?.html_content) {
        saveEdit(
          {
            path: { minute_id: minute.id! },
            body: { html_content: data.html, content_source: 'manual_edit' },
          },
          {
            onSuccess,
          }
        )
      }
      {
        setIsEditable(false)
      }
    },
    [minute.id, displayedMinuteVersion?.html_content, onSuccess, saveEdit]
  )
  const handleWordDocDownload = useCallback(() => {
    posthog.capture('minutes_downloaded', {
      format: 'word',
      version_id: displayedMinuteVersion?.id,
    })

    convertAIMinutesToWordDoc(
      htmlContent,
      transcription.dialogue_entries || [],
      transcription.title || 'minutes.docx'
    )
  }, [
    htmlContent,
    displayedMinuteVersion?.id,
    transcription.dialogue_entries,
    transcription.title,
  ])

  if (isLoading) {
    return (
      <div className="flex flex-col items-center">
        <p>Loading...</p>
      </div>
    )
  }

  if (!displayedMinuteVersion || isErrorFetchingVersions) {
    return (
      <>
        <GovukNotificationBanner
          variant="important"
          title="There is a problem"
          className="govuk-!-margin-bottom-2"
        >
          There has been an error loading this document.
        </GovukNotificationBanner>
        <GovukButton variant="secondary" onClick={() => refetch()}>
          Retry
        </GovukButton>
      </>
    )
  }
  if (isGenerating) {
    const isAiEdit = displayedMinuteVersion?.content_source === 'ai_edit'
    return (
      <div className="pt-2">
        <div className="mb-2 flex flex-wrap justify-between gap-y-2">
          <div className="flex flex-wrap gap-2">
            <MinuteVersionSelect
              minuteVersions={minuteVersions}
              version={version}
              setVersion={setVersion}
            />
          </div>
        </div>
        {isAiEdit ? (
          <div className="flex flex-col items-center justify-center gap-4 py-16">
            <LoaderCircle
              size={64}
              className="animate-spin"
              aria-hidden="true"
            />
            <p className="govuk-body" role="status">
              Applying AI edits to ‘{minute.template_name}’…
            </p>
          </div>
        ) : (
          <div className="flex h-36 animate-pulse flex-col items-center justify-center pt-12">
            <FilePenLine />
            Minute generating...
          </div>
        )}
      </div>
    )
  }
  if (isError) {
    return (
      <div className="pt-2">
        <div className="mb-2 flex flex-wrap justify-between gap-y-2">
          <div className="flex flex-wrap gap-2">
            <MinuteVersionSelect
              minuteVersions={minuteVersions}
              version={version}
              setVersion={setVersion}
            />
          </div>
        </div>
        <div className="mx-auto pt-12">
          <GovukNotificationBanner
            variant="important"
            title="There is a problem"
            className="mb-[15px]!"
          >
            <p className="govuk-notification-banner__heading">
              {minuteVersions.length > 1
                ? 'There was a problem processing your request. Click undo to go back to the previous version.'
                : 'There was a problem processing your request. Try generating a new Minute.'}
            </p>
          </GovukNotificationBanner>
          {minuteVersions.length > 1 ? (
            <MinuteVersionDeleteButton minuteVersion={displayedMinuteVersion} />
          ) : (
            <NewMinuteDialog
              transcriptionId={transcription.id!}
              agenda={minute.agenda ?? undefined}
            />
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="pt-2">
      <GovukButtonGroup>
        <AiEditPopover
          disabled={isEditable}
          minuteId={minute.id!}
          minuteVersionId={displayedMinuteVersion.id}
          onSuccess={onSuccess}
          onEditStart={() => {
            setEditSourceVersionId(displayedMinuteVersion.id)
          }}
        />
        {isEditable ? (
          <GovukButton
            onClick={form.handleSubmit(onSubmit)}
            variant="secondary"
          >
            Save Changes
          </GovukButton>
        ) : (
          <GovukButton variant="secondary" onClick={() => setIsEditable(true)}>
            Manual edit
          </GovukButton>
        )}
        <GovukButton onClick={handleWordDocDownload} variant="secondary">
          Download document
        </GovukButton>
        <CopyButton
          textToCopy={contentToCopy}
          posthogEvent={'editor_content_copied'}
          label="Copy document"
        />
        {hasCitations && (
          <GovukButton
            variant="secondary"
            onClick={() => setHideCitations((h) => !h)}
            disabled={isEditable}
          >
            {isEditable
              ? 'Quotes shown when editing'
              : hideCitations
                ? 'Show quotes'
                : 'Hide quotes'}
          </GovukButton>
        )}
      </GovukButtonGroup>
      <MinuteVersionSelect
        version={displayedMinuteVersion.id}
        setVersion={setVersion}
        minuteVersions={minuteVersions}
      />
      <hr className="govuk-section-break govuk-section-break--visible govuk-!-margin-top-6 govuk-!-margin-bottom-6" />
      {!displayedMinuteVersion.too_short &&
        displayedMinuteVersion.guardrail_results && (
          <GuardrailResponseComponent
            guardrailResults={displayedMinuteVersion.guardrail_results}
          />
        )}
      <form onSubmit={form.handleSubmit(onSubmit)}>
        <Controller
          control={form.control}
          name="html"
          render={({ field: { onChange } }) => (
            <SimpleEditor
              currentTranscription={transcription}
              initialContent={displayedMinuteVersion.html_content || ''}
              isEditing={isEditable}
              onContentChange={onChange}
              hideCitations={hideCitations && !isEditable}
            />
          )}
        />
      </form>
    </div>
  )
}

const MinuteVersionDeleteButton = ({
  minuteVersion,
  className,
}: {
  minuteVersion: MinuteVersionResponse
  className?: string
}) => {
  const queryClient = useQueryClient()
  const { mutate, isPending } = useMutation({
    ...deleteMinuteVersionMinuteVersionsMinuteVersionIdDeleteMutation(),
    onSuccess() {
      queryClient.invalidateQueries({
        queryKey: listMinuteVersionsMinutesMinuteIdVersionsGetQueryKey({
          path: { minute_id: minuteVersion.minute_id },
        }),
      })
      posthog.capture('deleted_minute_version', {
        minuteVersionId: minuteVersion.id,
      })
    },
  })
  return (
    <GovukButton
      variant="secondary"
      onClick={() => mutate({ path: { minute_version_id: minuteVersion.id } })}
      className={className}
    >
      {isPending ? (
        <>
          <Loader2 className="animate-spin" /> Deleting
        </>
      ) : (
        <>Undo</>
      )}
    </GovukButton>
  )
}
