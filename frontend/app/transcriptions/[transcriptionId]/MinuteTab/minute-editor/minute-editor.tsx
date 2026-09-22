'use client'

import SimpleEditor from '@/app/transcriptions/[transcriptionId]/MinuteTab/components/editor/tiptap-editor'
import { MinuteVersionSelect } from '@/app/transcriptions/[transcriptionId]/MinuteTab/minute-editor/minute-version-select'
import { NewMinuteDialog } from '@/app/transcriptions/[transcriptionId]/MinuteTab/NewMinuteDialog'
import { ReviewGuardButton } from '@/components/review-guard/review-guard-button'
import { ProcessingSpinner } from '@/components/processing-spinner'
import { citationRegex, citationRegexWithSpace } from '@/lib/citationRegex'
import {
  Minute,
  MinuteVersionResponse,
  TranscriptionGetResponse,
} from '@/lib/client'
import {
  createMinuteVersionMinutesMinuteIdVersionsPostMutation,
  deleteMinuteVersionMinuteVersionsMinuteVersionIdDeleteMutation,
  getGuardrailWarningMinuteVersionsMinuteVersionIdGuardrailsGetOptions,
  listMinuteVersionsMinutesMinuteIdVersionsGetOptions,
  listMinuteVersionsMinutesMinuteIdVersionsGetQueryKey,
} from '@/lib/client/@tanstack/react-query.gen'
import convertAIMinutesToWordDoc from '@/lib/download-word-doc'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Loader2 } from 'lucide-react'
import posthog from 'posthog-js'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Controller, useForm, useWatch } from 'react-hook-form'
import {
  GovukButton,
  GovukButtonGroup,
  GovukModalDialogue,
  GovukModalDialogueActions,
  GovukNotificationBanner,
  GovukWarningText,
} from '@/components/govuk'
import { AiEditPopover } from '@/app/transcriptions/[transcriptionId]/MinuteTab/minute-editor/ai-edit-popover'
import { Banner, useBannerStore } from '@/stores/use-banner-store'
import { copyHTML, formatDate } from '@/lib/utils'

type MinuteEditorForm = {
  html: string
}

export function MinuteEditor({
  transcription,
  minute,
  onActivityChange,
  onCitationClicked,
}: {
  transcription: TranscriptionGetResponse
  minute: Minute
  onActivityChange?: (busy: boolean) => void
  onCitationClicked?: (citationIndex: number) => void
}) {
  const [versionId, setVersionId] = useState<string | undefined>(undefined)
  const [editSourceVersionId, setEditSourceVersionId] = useState<
    string | undefined
  >(undefined)
  const [hideCitations, setHideCitations] = useState(false)
  const { setBanner } = useBannerStore()
  const previousMinuteVersionsRef = useRef<MinuteVersionResponse[]>([])

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
      const currentVersion = data.find((v) => v.id === versionId) ?? data[0]
      return ['awaiting_start', 'in_progress'].includes(currentVersion.status)
        ? 1000
        : false
    },
  })

  const determineMinuteVersionToShow = () => {
    if (minuteVersions.length === 0) {
      return undefined
    }

    const selectedVersion = minuteVersions.find((v) => v.id === versionId)

    if (selectedVersion) {
      return selectedVersion
    }

    const latestVersion = minuteVersions[0]
    const editSourceVersion = minuteVersions.find(
      (v) => v.id === editSourceVersionId
    )

    if (latestVersion.status === 'failed' && !!editSourceVersion) {
      return editSourceVersion
    }

    return minuteVersions.find((v) => v.status !== 'failed') ?? latestVersion
  }

  const displayedMinuteVersion = determineMinuteVersionToShow()
  const { data: guardrailWarning } = useQuery({
    ...getGuardrailWarningMinuteVersionsMinuteVersionIdGuardrailsGetOptions({
      path: { minute_version_id: displayedMinuteVersion?.id ?? '' },
    }),
    enabled:
      !!displayedMinuteVersion &&
      displayedMinuteVersion.status === 'completed' &&
      !displayedMinuteVersion.too_short,
  })

  const isGenerating = ['awaiting_start', 'in_progress'].includes(
    displayedMinuteVersion?.status || ''
  )

  const isError = displayedMinuteVersion?.status == 'failed'

  // Busy if any version is generating, not just the viewed one, so a background AI edit still counts.
  const isAnyVersionGenerating = useMemo(
    () =>
      minuteVersions.some((v) =>
        ['awaiting_start', 'in_progress'].includes(v.status)
      ),
    [minuteVersions]
  )

  useEffect(() => {
    const banner = getTransitionBanner(
      previousMinuteVersionsRef.current,
      minuteVersions,
      minute.template_name
    )
    if (banner) {
      setBanner(banner)
    }

    previousMinuteVersionsRef.current = minuteVersions
  }, [minuteVersions, minute.template_name, setBanner])

  const queryClient = useQueryClient()
  const [isEditable, setIsEditable] = useState(false)
  const [showDiscardModal, setShowDiscardModal] = useState(false)
  // The editor only reads initialContent on mount, so bumping this key discards its edits.
  const [editorResetKey, setEditorResetKey] = useState(0)
  const form = useForm<MinuteEditorForm>()
  useEffect(() => {
    if (displayedMinuteVersion) {
      form.setValue('html', displayedMinuteVersion.html_content)
    }
  }, [form, displayedMinuteVersion])

  useEffect(() => {
    onActivityChange?.(isAnyVersionGenerating || isEditable)
  }, [isAnyVersionGenerating, isEditable, onActivityChange])
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
    setVersionId(undefined)
    queryClient.invalidateQueries({
      queryKey: listMinuteVersionsMinutesMinuteIdVersionsGetQueryKey({
        path: { minute_id: minute.id! },
      }),
    })
  }, [minute.id, queryClient])

  const onSubmit = useCallback(
    (data: MinuteEditorForm) => {
      if (data.html === displayedMinuteVersion?.html_content) {
        setIsEditable(false)
        return
      }
      saveEdit(
        {
          path: { minute_id: minute.id! },
          body: { html_content: data.html, content_source: 'manual_edit' },
        },
        {
          onSuccess: () => {
            onSuccess()
            setBanner({
              variant: 'success',
              title: 'Success',
              message: `Manual edits to ‘${minute.template_name}’ saved`,
            })
          },
          onError: () => {
            setBanner({
              variant: 'important',
              title: 'There is a problem',
              message:
                'Something went wrong saving your edits. Please try again.',
            })
          },
        }
      )
    },
    [
      minute.id,
      minute.template_name,
      displayedMinuteVersion?.html_content,
      onSuccess,
      saveEdit,
      setBanner,
    ]
  )

  const handleCancelEdits = () => {
    if (htmlContent !== displayedMinuteVersion?.html_content) {
      setShowDiscardModal(true)
    } else {
      setIsEditable(false)
    }
  }

  const handleWordDocDownload = async () => {
    const fileName = transcription.date_of_recording
      ? `${minute.template_name} ${formatDate(transcription.date_of_recording)}.docx`
      : 'minutes.docx'

    return await convertAIMinutesToWordDoc(
      htmlContent,
      transcription.dialogue_entries || [],
      fileName
    )
  }

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
              version={versionId}
              setVersion={setVersionId}
            />
          </div>
        </div>
        {isAiEdit ? (
          <ProcessingSpinner
            label="Creating document"
            message={`Applying AI edits to '${minute.template_name}'...`}
          />
        ) : (
          <ProcessingSpinner
            label="Creating document"
            message={`Creating '${minute.template_name}'...`}
          />
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
              version={versionId}
              setVersion={setVersionId}
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
      <div>
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
          <GovukButton
            variant="secondary"
            onClick={() => setIsEditable(true)}
            disabled={isEditable}
          >
            Manual edit
          </GovukButton>
          <ReviewGuardButton
            onConfirm={async () => await copyHTML(contentToCopy)}
            onSuccess={() => {
              setBanner({
                variant: 'success',
                title: 'Success',
                message: `'${minute.template_name}' copied to clipboard`,
              })
              posthog.capture('editor_content_copied', {
                contentLength: contentToCopy.length,
              })
            }}
            action="copy"
            subject="document"
            disabled={isEditable}
          />
          <ReviewGuardButton
            onConfirm={handleWordDocDownload}
            onSuccess={() => {
              setBanner({
                variant: 'success',
                title: 'Success',
                message: `'${minute.template_name}' downloaded`,
              })
              posthog.capture('minutes_downloaded', {
                format: 'word',
                version_id: displayedMinuteVersion?.id,
              })
            }}
            action="download"
            subject="document"
            disabled={isEditable}
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
          setVersion={setVersionId}
          minuteVersions={minuteVersions}
          disabled={isEditable}
        />
      </div>
      {guardrailWarning?.message && (
        <div className="box-border flex w-full flex-col items-start gap-2 pt-[27px] pb-5">
          <GovukWarningText className="govuk-!-margin-bottom-0">
            {guardrailWarning.message}
          </GovukWarningText>
        </div>
      )}
      <hr
        className={
          guardrailWarning?.message
            ? 'govuk-section-break govuk-section-break--visible govuk-!-margin-top-0 govuk-!-margin-bottom-4'
            : 'govuk-section-break govuk-section-break--visible govuk-!-margin-top-6 govuk-!-margin-bottom-6'
        }
      />
      {isEditable && (
        <GovukButtonGroup className="govuk-!-margin-bottom-3">
          <GovukButton type="button" onClick={form.handleSubmit(onSubmit)}>
            Save edits
          </GovukButton>
          <GovukButton
            type="button"
            variant="warning"
            onClick={handleCancelEdits}
          >
            Cancel edits
          </GovukButton>
        </GovukButtonGroup>
      )}
      <form onSubmit={form.handleSubmit(onSubmit)}>
        <Controller
          control={form.control}
          name="html"
          render={({ field: { onChange } }) => (
            <SimpleEditor
              key={editorResetKey}
              currentTranscription={transcription}
              initialContent={displayedMinuteVersion.html_content || ''}
              isEditing={isEditable}
              onContentChange={onChange}
              hideCitations={hideCitations && !isEditable}
              onCitationClicked={onCitationClicked}
            />
          )}
        />
      </form>
      <GovukModalDialogue
        open={showDiscardModal}
        onClose={() => setShowDiscardModal(false)}
        title="Are you sure you want to discard your changes?"
      >
        <GovukModalDialogueActions>
          <GovukButton
            type="button"
            variant="warning"
            onClick={() => {
              setShowDiscardModal(false)
              setIsEditable(false)
              form.setValue('html', displayedMinuteVersion.html_content)
              setEditorResetKey((key) => key + 1)
            }}
          >
            Discard
          </GovukButton>
          <GovukButton
            type="button"
            variant="link"
            onClick={() => setShowDiscardModal(false)}
          >
            Cancel
          </GovukButton>
        </GovukModalDialogueActions>
      </GovukModalDialogue>
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

/** Detects an AI-edit completing/failing between two polled version snapshots. Returns the matching banner, or null. */
function getTransitionBanner(
  previousVersions: MinuteVersionResponse[],
  currentVersions: MinuteVersionResponse[],
  templateName: string | undefined | null
): Banner | null {
  const previousVersionsById = new Map(previousVersions.map((v) => [v.id, v]))
  const currentVersionsById = new Map(currentVersions.map((v) => [v.id, v]))

  for (const id of previousVersionsById.keys()) {
    const previous = previousVersionsById.get(id)
    const current = currentVersionsById.get(id)

    if (!previous || !current) {
      continue
    }

    // we return the first as we can only display one banner at a time, and a
    // user will normally only have one process at a time
    const justCompleted =
      previous.status !== 'completed' && current.status === 'completed'
    if (justCompleted) {
      if (current.content_source === 'ai_edit') {
        return {
          variant: 'success',
          title: 'Success',
          message: `AI edits to '${templateName}' saved`,
        }
      }
      if (current.content_source === 'initial_generation') {
        return {
          variant: 'success',
          title: 'Success',
          message: `'${templateName}' created.`,
        }
      }
    }

    const justFailed =
      previous?.status !== 'failed' && current.status === 'failed'
    if (justFailed) {
      if (current.content_source === 'ai_edit') {
        return {
          variant: 'important',
          title: 'There is a problem',
          message:
            'Something went wrong creating your AI Edit. Please try again.',
        }
      }
      if (current.content_source === 'initial_generation') {
        return {
          variant: 'important',
          title: 'There is a problem',
          message:
            'Something went wrong creating your document. Please try again.',
        }
      }
    }
  }

  return null
}
