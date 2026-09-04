'use client'

import SimpleEditor from '@/app/transcriptions/[transcriptionId]/MinuteTab/components/editor/tiptap-editor'
import { GuardrailResponseComponent } from '@/app/transcriptions/[transcriptionId]/MinuteTab/components/editor/guardrail-response-component'
import { MinuteVersionSelect } from '@/app/transcriptions/[transcriptionId]/MinuteTab/minute-editor/minute-version-select'
import { NewMinuteDialog } from '@/app/transcriptions/[transcriptionId]/MinuteTab/NewMinuteDialog'
import { Button } from '@/components/ui/button'
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
import { FilePenLine, FileX2, Loader2, Undo } from 'lucide-react'
import posthog from 'posthog-js'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { Controller, useForm, useWatch } from 'react-hook-form'
import {
  GovukButton,
  GovukButtonGroup,
  GovukModalDialogue,
  GovukModalDialogueActions,
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
    refetchInterval: (query) =>
      query.state.data &&
      query.state.data.length > 0 &&
      ['awaiting_start', 'in_progress'].includes(
        query.state.data.find((v) => v.id === version)?.status ??
          query.state.data[0].status
      )
        ? 1000
        : false,
  })

  const minuteVersion =
    minuteVersions.length > 0
      ? (minuteVersions.find((v) => v.id === version) ?? minuteVersions[0])
      : undefined

  const isGenerating = useMemo(
    () =>
      ['awaiting_start', 'in_progress'].includes(minuteVersion?.status || ''),
    [minuteVersion?.status]
  )
  const isError = useMemo(
    () => minuteVersion?.status == 'failed',
    [minuteVersion?.status]
  )

  const queryClient = useQueryClient()
  const [isEditable, setIsEditable] = useState(false)
  const [showDiscardModal, setShowDiscardModal] = useState(false)
  const setBanner = useBannerStore((store) => store.setBanner)
  const form = useForm<MinuteEditorForm>()
  useEffect(() => {
    if (minuteVersion) {
      form.setValue('html', minuteVersion.html_content)
    }
  }, [form, minuteVersion])
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
      if (data.html === minuteVersion?.html_content) {
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
      minuteVersion?.html_content,
      onSuccess,
      saveEdit,
      setBanner,
    ]
  )

  const handleCancelEdits = () => {
    if (htmlContent !== minuteVersion?.html_content) {
      setShowDiscardModal(true)
    } else {
      setIsEditable(false)
    }
  }

  const handleWordDocDownload = useCallback(() => {
    posthog.capture('minutes_downloaded', {
      format: 'word',
      version_id: minuteVersion?.id,
    })

    convertAIMinutesToWordDoc(
      htmlContent,
      transcription.dialogue_entries || [],
      transcription.title || 'minutes.docx'
    )
  }, [
    htmlContent,
    minuteVersion?.id,
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

  if (!minuteVersion || isErrorFetchingVersions) {
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
        <div className="flex h-36 animate-pulse flex-col items-center justify-center pt-12">
          <FilePenLine />
          Minute generating...
        </div>
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
        <div className="mx-auto flex flex-col items-center justify-center pt-12 text-center">
          <FileX2 />
          <p>There was a problem processing your request.</p>
          {minuteVersions.length > 1 ? (
            <>
              <p>Click undo to go back to the previous version.</p>
              <MinuteVersionDeleteButton minuteVersion={minuteVersion} />
            </>
          ) : (
            <>
              <p>Try generating a new Minute</p>
              <NewMinuteDialog
                transcriptionId={transcription.id!}
                agenda={minute.agenda ?? undefined}
              />
            </>
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
            minuteVersionId={minuteVersion.id}
            onSuccess={onSuccess}
          />
          <GovukButton
            variant="secondary"
            onClick={() => setIsEditable(true)}
            disabled={isEditable}
          >
            Manual edit
          </GovukButton>
          <GovukButton
            onClick={handleWordDocDownload}
            variant="secondary"
            disabled={isEditable}
          >
            Download document
          </GovukButton>
          <CopyButton
            textToCopy={contentToCopy}
            posthogEvent={'editor_content_copied'}
            label="Copy document"
            disabled={isEditable}
          />
          {hasCitations && (
            <GovukButton
              variant="secondary"
              onClick={() => setHideCitations((h) => !h)}
              disabled={isEditable}
            >
              {hideCitations ? 'Show quotes' : 'Hide quotes'}
            </GovukButton>
          )}
        </GovukButtonGroup>
        <MinuteVersionSelect
          version={minuteVersion.id}
          setVersion={setVersion}
          minuteVersions={minuteVersions}
          disabled={isEditable}
        />
      </div>
      <hr className="govuk-section-break govuk-section-break--visible govuk-!-margin-top-6 govuk-!-margin-bottom-6" />
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
      {!minuteVersion.too_short && minuteVersion.guardrail_results && (
        <GuardrailResponseComponent
          guardrailResults={minuteVersion.guardrail_results}
        />
      )}
      <form onSubmit={form.handleSubmit(onSubmit)}>
        <Controller
          control={form.control}
          name="html"
          render={({ field: { onChange } }) => (
            <SimpleEditor
              currentTranscription={transcription}
              initialContent={minuteVersion.html_content || ''}
              isEditing={isEditable}
              onContentChange={onChange}
              hideCitations={hideCitations && !isEditable}
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
              form.setValue('html', minuteVersion.html_content)
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
    <Button
      variant="outline"
      onClick={() => mutate({ path: { minute_version_id: minuteVersion.id } })}
      className={className}
    >
      {isPending ? (
        <>
          <Loader2 className="animate-spin" /> Deleting
        </>
      ) : (
        <>
          <Undo /> Undo
        </>
      )}
    </Button>
  )
}
