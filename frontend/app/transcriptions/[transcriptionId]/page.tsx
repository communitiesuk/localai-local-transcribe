'use client'

import { use, useCallback, useEffect, useRef, useState } from 'react'
import ChatTab from '@/app/transcriptions/[transcriptionId]/ChatTab/ChatTab'
import { MinuteTab } from '@/app/transcriptions/[transcriptionId]/MinuteTab/MinuteTab'
import { NewMinuteDialog } from '@/app/transcriptions/[transcriptionId]/MinuteTab/NewMinuteDialog'
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
import { StatusBadge } from '@/components/status-icon'
import { TranscriptionTitleEditor } from '@/components/transcription-title-editor'
import { TranscriptionGetResponse } from '@/lib/client'
import {
  getRecordingsForTranscriptionTranscriptionsTranscriptionIdRecordingsGetOptions,
  getTranscriptionTranscriptionsTranscriptionIdGetOptions,
  getTranscriptionTranscriptionsTranscriptionIdGetQueryKey,
  updateTranscriptionMetadataTranscriptionsTranscriptionIdDetailsPatchMutation,
} from '@/lib/client/@tanstack/react-query.gen'
import { FeatureFlags } from '@/lib/feature-flags'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { LoaderCircle } from 'lucide-react'
import { useFeatureFlagEnabled } from 'posthog-js/react'
import { redirect, useRouter } from 'next/navigation'
import { TranscriptionDetailsData } from '@/types/transcriptions'
import { FormProvider, useForm } from 'react-hook-form'
import { BannerNotification } from '@/components/banner-notification'
import { useBannerStore } from '@/stores/use-banner-store'

export default function TranscriptionPage(props: {
  params: Promise<{ transcriptionId: string }>
}) {
  const params = use(props.params)

  const { transcriptionId } = params

  const { setBanner, clearBanner } = useBannerStore()

  const isChatEnabled = useFeatureFlagEnabled(FeatureFlags.ChatEnabled)
  const [lineEditError, setLineEditError] = useState<string | null>(null)
  const errorSummaryRef = useRef<HTMLDivElement | null>(null)

  const [isTranscriptEditing, setIsTranscriptEditing] = useState(false)

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
  return (
    <div className="flex w-full flex-col">
      <GovukBackLink href="/transcriptions" className="govuk-!-margin-top-0">
        Back
      </GovukBackLink>
      <BannerNotification />
      {lineEditError && (
        <GovukErrorSummary
          ref={errorSummaryRef}
          errorList={[{ href: '#line-edit-actions', text: lineEditError }]}
        />
      )}
      <GovukHeading as="h1" size="xl" className="govuk-!-margin-bottom-2">
        {recordingDate}
      </GovukHeading>
      <hr className="govuk-section-break govuk-section-break--visible govuk-!-margin-top-2 govuk-!-margin-bottom-2" />
      <RecordingDetails
        dateTimeLabel={dateTimeLabel}
        transcription={transcription}
      />
      <hr className="govuk-section-break govuk-section-break--visible govuk-!-margin-top-2 govuk-!-margin-bottom-2" />
      <div>
        <NewMinuteDialog
          transcriptionId={transcription.id!}
          trigger={
            <GovukButton type="button" disabled={isTranscriptEditing}>
              Create document
            </GovukButton>
          }
        />
      </div>
      <GovukTabs id="transcription-tabs" className="govuk-!-margin-top-4">
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
      </GovukTabs>
    </div>
  )
}

const RecordingDetails = ({
  dateTimeLabel,
  transcription,
}: {
  dateTimeLabel: string
  transcription: TranscriptionGetResponse
}) => {
  const [open, setOpen] = useState(false)
  const router = useRouter()

  const clientDateOfBirth = new Date(transcription.client_date_of_birth)

  const form = useForm<TranscriptionDetailsData>({
    defaultValues: {
      clientName: transcription.client_name || undefined,
      caseId: transcription.case_id || undefined,
      subject: transcription.title || undefined,
      clientDateOfBirth: {
        day: clientDateOfBirth?.getDate().toString(),
        month: clientDateOfBirth
          ? (clientDateOfBirth.getMonth() + 1).toString()
          : undefined,
        year: clientDateOfBirth?.getFullYear().toString(),
      },
    },
  })

  const setBanner = useBannerStore((store) => store.setBanner)

  const queryClient = useQueryClient()

  const { mutate } = useMutation({
    ...updateTranscriptionMetadataTranscriptionsTranscriptionIdDetailsPatchMutation(),
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
    },
  })

  const handleSave = (data: TranscriptionDetailsData) => {
    let dateOfBirth = undefined
    if (
      data.clientDateOfBirth.day &&
      data.clientDateOfBirth.month &&
      data.clientDateOfBirth.year
    ) {
      dateOfBirth = new Date(
        parseInt(data.clientDateOfBirth.year),
        parseInt(data.clientDateOfBirth.month) - 1,
        parseInt(data.clientDateOfBirth.day)
      )
    }

    mutate({
      path: { transcription_id: transcription.id },
      body: {
        client_name: data.clientName,
        case_id: data.caseId,
        subject: data.subject,
        client_date_of_birth: dateOfBirth?.toISOString(),
      },
    })
    form.reset(data)
  }

  return (
    <>
      <GovukHeading as="h2" size="s" className="govuk-!-margin-bottom-2">
        Recording details
      </GovukHeading>
      <GovukDetails
        summary={open ? 'Hide' : 'Show'}
        onToggle={(e) => setOpen(e.currentTarget.open)}
      >
        <p className="govuk-body govuk-!-margin-bottom-1">Date recorded:</p>
        <p className="govuk-body govuk-!-font-weight-bold">{dateTimeLabel}</p>
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
                disabled={!form.formState.isDirty}
              >
                Update details
              </GovukButton>
              <GovukButton
                type="button"
                variant="warning"
                className="govuk-!-margin-bottom-0"
                onClick={() => router.push(`${transcription.id}/delete`)}
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
