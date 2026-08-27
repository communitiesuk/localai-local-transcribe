'use client'

import { use, useCallback, useEffect, useRef, useState } from 'react'
import ChatTab from '@/app/transcriptions/[transcriptionId]/ChatTab/ChatTab'
import { MinuteTab } from '@/app/transcriptions/[transcriptionId]/MinuteTab/MinuteTab'
import { NewDocumentTab } from '@/app/transcriptions/[transcriptionId]/NewDocumentTab/NewDocumentTab'
import { TranscriptionTab } from '@/app/transcriptions/[transcriptionId]/TranscriptionTab/TranscriptionTab'
import { DownloadButton } from '@/components/download-button'
import {
  GovukBackLink,
  GovukButton,
  GovukButtonGroup,
  GovukDateInput,
  GovukDetails,
  GovukErrorSummary,
  GovukFormGroup,
  GovukHeading,
  GovukInput,
  GovukLabel,
  GovukNotificationBanner,
  GovukTabs,
} from '@/components/govuk'
import { validateDateEntry } from '@/components/govuk/date-input'
import { StatusBadge } from '@/components/status-icon'
import { TranscriptionTitleEditor } from '@/components/transcription-title-editor'
import { TranscriptionGetResponse } from '@/lib/client'
import {
  getRecordingsForTranscriptionTranscriptionsTranscriptionIdRecordingsGetOptions,
  getTranscriptionTranscriptionsTranscriptionIdGetOptions,
  getTranscriptionTranscriptionsTranscriptionIdGetQueryKey,
  updateTranscriptionMetadataTranscriptionsTranscriptionIdDetailsPutMutation,
} from '@/lib/client/@tanstack/react-query.gen'
import { FeatureFlags } from '@/lib/feature-flags'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { LoaderCircle } from 'lucide-react'
import { useFeatureFlagEnabled } from 'posthog-js/react'
import { redirect, useRouter } from 'next/navigation'
import { TranscriptionDetailsData } from '@/types/transcriptions'
import { FormProvider, useForm, useWatch } from 'react-hook-form'
import { BannerNotification } from '@/components/banner-notification'
import { useBannerStore } from '@/stores/use-banner-store'
import { useTranscriptionDetailsDraftStore } from '@/stores/use-transcription-details-draft-store'
import type { ErrorItem } from '@/components/govuk/error-summary'

export default function TranscriptionPage(props: {
  params: Promise<{ transcriptionId: string }>
}) {
  const params = use(props.params)

  const { transcriptionId } = params

  const { setBanner, clearBanner } = useBannerStore()

  const isChatEnabled = useFeatureFlagEnabled(FeatureFlags.ChatEnabled)
  const [lineEditError, setLineEditError] = useState<string | null>(null)
  const [recordingDetailsErrors, setRecordingDetailsErrors] = useState<
    ErrorItem[]
  >([])
  const errorSummaryRef = useRef<HTMLDivElement | null>(null)

  const [isTranscriptEditing, setIsTranscriptEditing] = useState(false)

  const [activeTab, setActiveTab] = useState('transcript')
  const [documentTabs, setDocumentTabs] = useState<
    { id: string; label: string }[]
  >([])
  const documentCounter = useRef(0)

  const handleLineEditError = useCallback((error: string | null) => {
    setLineEditError(error)
  }, [])

  useEffect(() => {
    if (lineEditError && errorSummaryRef.current) {
      errorSummaryRef.current.scrollIntoView({
        behavior: 'smooth',
        block: 'start',
      })
    }
  }, [lineEditError])

  const { data: transcription, isLoading } = useQuery({
    ...getTranscriptionTranscriptionsTranscriptionIdGetOptions({
      path: { transcription_id: transcriptionId },
    }),
    refetchInterval: (query) =>
      query.state.data?.status &&
      ['awaiting_start', 'in_progress'].includes(query.state.data.status)
        ? 2000
        : false,
    refetchOnWindowFocus: false,
  })

  if (!transcription && !isLoading) {
    redirect('/')
  }

  if (isLoading) {
    return (
      <div className="flex h-72 flex-col items-center justify-center">
        <LoaderCircle size={80} className="animate-spin" aria-hidden="true" />
      </div>
    )
  }

  if (!transcription) {
    return (
      <div className="govuk-grid-row">
        <div className="govuk-grid-column-two-thirds">
          <GovukHeading>Transcription not found</GovukHeading>
          <p className="govuk-body">
            We could not find that transcription. It may have been deleted.
          </p>
        </div>
      </div>
    )
  }

  const dateString =
    transcription.date_of_recording ?? transcription.created_datetime
  const date = new Date(dateString)
  const dateLabel = `${date.toDateString()} at ${date.toLocaleTimeString()}`
  const recordingDate = date.toLocaleDateString('en-GB')
  const dateTimeLabel = `${date.toLocaleDateString('en-GB')} at ${date.toLocaleTimeString('en-GB')}`

  if (
    transcription.status &&
    ['awaiting_start', 'in_progress'].includes(transcription.status)
  ) {
    return (
      <div>
        <TranscriptionHeader
          transcription={transcription}
          dateLabel={dateLabel}
        />
        <GovukNotificationBanner title="Processing">
          <p className="govuk-notification-banner__heading">
            Your transcription is being processed. You can close the tab and
            come back later.
          </p>
        </GovukNotificationBanner>
        <AudioPlayer transcriptionId={transcription.id} />
      </div>
    )
  }

  if (transcription.status == 'failed') {
    return (
      <div>
        <TranscriptionHeader
          transcription={transcription}
          dateLabel={dateLabel}
        />
        <GovukNotificationBanner title="Transcription failed">
          <p className="govuk-notification-banner__heading">
            Something went wrong with your transcription. You may need to try
            again.
          </p>
        </GovukNotificationBanner>
        <AudioPlayer transcriptionId={transcription.id} />
      </div>
    )
  }
  const handleCreateDocument = () => {
    const id = `new-document-${documentCounter.current++}`
    setDocumentTabs((prev) => [...prev, { id, label: 'New document' }])
    setActiveTab(id)
  }

  const removeDocumentTab = (id: string) => {
    setDocumentTabs((prev) => prev.filter((tab) => tab.id !== id))
    setActiveTab('transcript')
  }

  const handleDocumentCreated = (id: string, templateName: string) => {
    setDocumentTabs((prev) =>
      prev.map((tab) => (tab.id === id ? { ...tab, label: templateName } : tab))
    )
  }

  return (
    <div className="flex w-full flex-col">
      <GovukBackLink href="/transcriptions" className="govuk-!-margin-top-0">
        Back
      </GovukBackLink>
      <BannerNotification />
      {(lineEditError || recordingDetailsErrors.length > 0) && (
        <GovukErrorSummary
          ref={errorSummaryRef}
          errorList={[
            ...(lineEditError
              ? [{ href: '#line-edit-actions', text: lineEditError }]
              : []),
            ...recordingDetailsErrors,
          ]}
        />
      )}
      <GovukHeading as="h1" size="xl" className="govuk-!-margin-bottom-2">
        {recordingDate}
      </GovukHeading>
      <hr className="govuk-section-break govuk-section-break--visible govuk-!-margin-top-2 govuk-!-margin-bottom-2" />
      <RecordingDetails
        dateTimeLabel={dateTimeLabel}
        transcription={transcription}
        onErrorListChange={setRecordingDetailsErrors}
      />
      <hr className="govuk-section-break govuk-section-break--visible govuk-!-margin-top-2 govuk-!-margin-bottom-2" />
      <div>
        <GovukButton
          type="button"
          disabled={isTranscriptEditing}
          onClick={handleCreateDocument}
        >
          Create document
        </GovukButton>
      </div>
      <GovukTabs
        id="transcription-tabs"
        className="govuk-!-margin-top-4"
        activeTab={activeTab}
        onTabChange={setActiveTab}
      >
        <GovukTabs.Panel id="transcript" label="Transcript">
          <TranscriptionTab
            transcription={transcription}
            onTranscriptCopied={() =>
              setBanner({
                variant: 'success',
                title: 'Success',
                message: 'Transcript copied to clipboard.',
              })
            }
            onTranscriptDownloaded={() =>
              setBanner({
                variant: 'success',
                title: 'Success',
                message: 'Transcript downloaded.',
              })
            }
            onDismissBanner={clearBanner}
            onLineEditError={handleLineEditError}
            onEditModeChange={setIsTranscriptEditing}
          />
        </GovukTabs.Panel>
        <GovukTabs.Panel id="meeting-summary" label="Meeting summary">
          <MinuteTab transcription={transcription} />
        </GovukTabs.Panel>
        {isChatEnabled && (
          <GovukTabs.Panel id="chat" label="Chat with your meeting">
            <ChatTab transcription={transcription} />
          </GovukTabs.Panel>
        )}
        {documentTabs.map((tab) => (
          <GovukTabs.Panel key={tab.id} id={tab.id} label={tab.label}>
            <NewDocumentTab
              transcription={transcription}
              onCancel={() => removeDocumentTab(tab.id)}
              onCreated={(templateName) =>
                handleDocumentCreated(tab.id, templateName)
              }
            />
          </GovukTabs.Panel>
        ))}
      </GovukTabs>
    </div>
  )
}

const formatDateTimeLocalValue = (dateString: string | null | undefined) => {
  if (!dateString) return ''

  const date = new Date(dateString)
  if (Number.isNaN(date.getTime())) return ''

  const timezoneOffsetMs = date.getTimezoneOffset() * 60_000
  return new Date(date.getTime() - timezoneOffsetMs).toISOString().slice(0, 19)
}

const formatDateInputValue = (dateString: string | null | undefined) => {
  const dateTimeValue = formatDateTimeLocalValue(dateString)
  if (!dateTimeValue) return { day: '', month: '', year: '' }

  const [year, month, day] = dateTimeValue.split('T')[0].split('-')
  return {
    day: String(Number(day)),
    month: String(Number(month)),
    year,
  }
}

const formatTimeInputValue = (dateString: string | null | undefined) => {
  const dateTimeValue = formatDateTimeLocalValue(dateString)
  if (!dateTimeValue) return ''
  return dateTimeValue.split('T')[1].slice(0, 5)
}

const formatRecordingDateForSave = (
  dateValue: { day: string; month: string; year: string },
  timeValue: string,
  existingDateString: string | null | undefined
) => {
  if (!dateValue.day && !dateValue.month && !dateValue.year) return null

  const existingTime =
    formatDateTimeLocalValue(existingDateString).split('T')[1] ?? '00:00:00'
  const time = /^([01]\d|2[0-3]):[0-5]\d$/.test(timeValue)
    ? `${timeValue}:00`
    : existingTime

  return `${dateValue.year.padStart(4, '0')}-${dateValue.month.padStart(2, '0')}-${dateValue.day.padStart(2, '0')}T${time}`
}

const RecordingDetails = ({
  dateTimeLabel,
  onErrorListChange,
  transcription,
}: {
  dateTimeLabel: string
  onErrorListChange: (errors: ErrorItem[]) => void
  transcription: TranscriptionGetResponse
}) => {
  const { draft, setDraft, clearDraft } = useTranscriptionDetailsDraftStore()
  const [open, setOpen] = useState(
    (draft?.transcriptionId === transcription.id && draft?.isOpen) ?? false
  )
  const router = useRouter()
  const isUpload = transcription.is_upload === true

  let clientDateOfBirth: Date | null = null
  if (transcription.client_date_of_birth) {
    clientDateOfBirth = new Date(transcription.client_date_of_birth)
  }

  const form = useForm<TranscriptionDetailsData>({
    mode: 'onChange',
    reValidateMode: 'onChange',
    defaultValues: {
      dateOfRecording: formatDateInputValue(
        transcription.date_of_recording ?? transcription.created_datetime
      ),
      dateOfRecordingTime: formatTimeInputValue(
        transcription.date_of_recording ?? transcription.created_datetime
      ),
      clientName: transcription.client_name || '',
      caseId: transcription.case_id || '',
      subject: transcription.title || '',
      clientDateOfBirth: {
        day: clientDateOfBirth?.getUTCDate().toString() || '',
        month: clientDateOfBirth
          ? (clientDateOfBirth.getUTCMonth() + 1).toString()
          : '',
        year: clientDateOfBirth?.getUTCFullYear().toString() || '',
      },
    },
  })
  const dateOfRecording = useWatch({
    control: form.control,
    name: 'dateOfRecording',
  })
  useEffect(() => {
    if (draft?.transcriptionId === transcription.id) {
      form.reset(draft.data, { keepDefaultValues: true })
    }
  }, [draft, transcription.id, form])

  const { dirtyFields, errors, isSubmitted } = form.formState
  const dateOfRecordingError = isUpload
    ? validateDateEntry(dateOfRecording, 'past', 'date recorded', true)
    : null
  const dateOfRecordingMessage = errors.dateOfRecording?.message
  const dateOfRecordingTimeMessage = errors.dateOfRecordingTime?.message
  const clientDateOfBirthMessage = errors.clientDateOfBirth?.message

  const shouldShowErrorSummary =
    (isSubmitted ||
      (dirtyFields.clientDateOfBirth && !!clientDateOfBirthMessage) ||
      (isUpload &&
        (!!dirtyFields.dateOfRecording || !!dirtyFields.dateOfRecordingTime) &&
        (!!dateOfRecordingMessage || !!dateOfRecordingTimeMessage))) &&
    (!!dateOfRecordingMessage ||
      !!dateOfRecordingTimeMessage ||
      !!clientDateOfBirthMessage)

  useEffect(() => {
    const errorList = [
      dateOfRecordingMessage && {
        href: '#date-recorded-day',
        text: dateOfRecordingMessage,
      },
      dateOfRecordingTimeMessage && {
        href: '#time-recorded',
        text: dateOfRecordingTimeMessage,
      },
      clientDateOfBirthMessage && {
        href: '#client-dob-day',
        text: clientDateOfBirthMessage,
      },
    ].filter(Boolean) as ErrorItem[]

    onErrorListChange(shouldShowErrorSummary ? errorList : [])
  }, [
    clientDateOfBirthMessage,
    dateOfRecordingMessage,
    dateOfRecordingTimeMessage,
    onErrorListChange,
    shouldShowErrorSummary,
  ])

  const setBanner = useBannerStore((store) => store.setBanner)

  const queryClient = useQueryClient()

  const { mutate } = useMutation({
    ...updateTranscriptionMetadataTranscriptionsTranscriptionIdDetailsPutMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: getTranscriptionTranscriptionsTranscriptionIdGetQueryKey({
          path: { transcription_id: transcription.id },
        }),
      })
      setBanner({
        variant: 'success',
        title: 'Success',
        message: 'Recording details updated',
      })
      clearDraft()
      form.reset(form.getValues())
    },
  })

  const handleSave = (data: TranscriptionDetailsData) => {
    let dateOfBirth: Date | null = null
    if (
      data.clientDateOfBirth.day &&
      data.clientDateOfBirth.month &&
      data.clientDateOfBirth.year
    ) {
      dateOfBirth = new Date(
        Date.UTC(
          parseInt(data.clientDateOfBirth.year),
          parseInt(data.clientDateOfBirth.month) - 1,
          parseInt(data.clientDateOfBirth.day)
        )
      )
    }

    mutate({
      path: { transcription_id: transcription.id },
      body: {
        client_name: data.clientName || null,
        case_id: data.caseId || null,
        subject: data.subject || null,
        client_date_of_birth: dateOfBirth ? dateOfBirth.toISOString() : null,
        date_of_recording:
          isUpload &&
          (dirtyFields.dateOfRecording || dirtyFields.dateOfRecordingTime)
            ? formatRecordingDateForSave(
                data.dateOfRecording,
                data.dateOfRecordingTime,
                transcription.date_of_recording ??
                  transcription.created_datetime
              )
            : (transcription.date_of_recording ?? null),
      },
    })
  }
  return (
    <>
      <GovukHeading as="h2" size="s" className="govuk-!-margin-bottom-2">
        Recording details
      </GovukHeading>
      <GovukDetails
        open={open}
        summary={open ? 'Hide' : 'Show'}
        onToggle={(e) => setOpen(e.currentTarget.open)}
      >
        {isUpload ? (
          <>
            <GovukDateInput
              id="date-recorded"
              legend="Date recorded"
              control={form.control}
              name={'dateOfRecording'}
              mustBePastOrFuture={'past'}
              description="date recorded"
              required
            />
            <GovukFormGroup hasError={!!errors.dateOfRecordingTime}>
              <GovukLabel htmlFor="time-recorded">Time recorded</GovukLabel>
              {errors.dateOfRecordingTime?.message && (
                <p className="govuk-error-message">
                  <span className="govuk-visually-hidden">Error:</span>{' '}
                  {errors.dateOfRecordingTime.message}
                </p>
              )}
              <GovukInput
                id="time-recorded"
                className="govuk-input--width-5"
                inputMode="numeric"
                placeholder="HH:MM"
                {...form.register('dateOfRecordingTime', {
                  validate: (value) => {
                    if (!isUpload) return true
                    if (!value.trim()) {
                      return 'The time recorded must include hours and minutes'
                    }
                    if (!/^([01]\d|2[0-3]):[0-5]\d$/.test(value)) {
                      return 'The time recorded must be in the format HH:MM'
                    }
                    return true
                  },
                })}
              />
            </GovukFormGroup>
          </>
        ) : (
          <>
            <p className="govuk-body govuk-!-margin-bottom-1">Date recorded:</p>
            <p className="govuk-body govuk-!-font-weight-bold">
              {dateTimeLabel}
            </p>
          </>
        )}
        <FormProvider {...form}>
          <form onSubmit={form.handleSubmit(handleSave)} noValidate>
            <GovukFormGroup>
              <GovukLabel htmlFor="client-name">
                Client name (optional)
              </GovukLabel>
              <GovukInput id="client-name" {...form.register('clientName')} />
            </GovukFormGroup>
            <GovukFormGroup>
              <GovukLabel htmlFor="case-id">Case ID (optional)</GovukLabel>
              <GovukInput id="case-id" {...form.register('caseId')} />
            </GovukFormGroup>
            <GovukFormGroup>
              <GovukLabel htmlFor="subject">Subject (optional)</GovukLabel>
              <GovukInput id="subject" {...form.register('subject')} />
            </GovukFormGroup>
            <GovukDateInput
              id="client-dob"
              legend="Client date of birth (optional)"
              control={form.control}
              name={'clientDateOfBirth'}
              mustBePastOrFuture={'past'}
              description={"client's date of birth"}
            />
            <GovukButtonGroup>
              <GovukButton
                type="submit"
                variant="secondary"
                className="govuk-!-margin-bottom-2"
                disabled={
                  !form.formState.isDirty ||
                  !!dateOfRecordingError ||
                  !!errors.dateOfRecordingTime
                }
              >
                Update details
              </GovukButton>
              <GovukButton
                type="button"
                variant="warning"
                className="govuk-!-margin-bottom-0"
                onClick={() => {
                  setDraft({
                    transcriptionId: transcription.id,
                    data: form.getValues(),
                    isOpen: open,
                  })
                  router.push(`${transcription.id}/delete`)
                }}
              >
                Delete recording
              </GovukButton>
            </GovukButtonGroup>
          </form>
        </FormProvider>
      </GovukDetails>
    </>
  )
}

const TranscriptionHeader = ({
  transcription,
  dateLabel,
}: {
  transcription: TranscriptionGetResponse
  dateLabel: string
}) => (
  <>
    <TranscriptionTitleEditor
      title={transcription.title}
      transcriptionId={transcription.id}
      status={transcription.status}
    />
    <div className="govuk-!-margin-bottom-4 flex items-center gap-2">
      <StatusBadge status={transcription.status} />
      <span className="govuk-body-s govuk-!-margin-bottom-0">{dateLabel}</span>
    </div>
  </>
)

const AudioPlayer = ({ transcriptionId }: { transcriptionId: string }) => {
  const { data: recordings } = useQuery({
    ...getRecordingsForTranscriptionTranscriptionsTranscriptionIdRecordingsGetOptions(
      { path: { transcription_id: transcriptionId } }
    ),
  })
  if (!recordings || recordings.length == 0) {
    return null
  }
  return (
    <div className="mb-2 flex w-full max-w-3xl flex-col gap-2 rounded border bg-white p-2">
      <audio controls src={recordings[0].url} className="w-full" />
      <div className="flex justify-end">
        <DownloadButton recordings={recordings} />
      </div>
    </div>
  )
}
