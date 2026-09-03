'use client'

import { use, useCallback, useEffect, useRef, useState } from 'react'
import ChatTab from '@/app/transcriptions/[transcriptionId]/ChatTab/ChatTab'
import { MinuteTab } from '@/app/transcriptions/[transcriptionId]/MinuteTab/MinuteTab'
import { DocumentTab } from '@/app/transcriptions/[transcriptionId]/NewDocumentTab/DocumentTab'
import { NewDocumentTab } from '@/app/transcriptions/[transcriptionId]/NewDocumentTab/NewDocumentTab'
import { TranscriptionTab } from '@/app/transcriptions/[transcriptionId]/TranscriptionTab/TranscriptionTab'
import { RecordingDetails } from '@/app/transcriptions/[transcriptionId]/RecordingDetails'
import { isTranscriptionProcessing } from '@/app/transcriptions/[transcriptionId]/TranscriptionStatus'
import { StatusNotificationPage } from '@/app/transcriptions/[transcriptionId]/TranscriptionHeader'
import {
  GovukButton,
  GovukErrorSummary,
  GovukHeading,
  GovukTabs,
} from '@/components/govuk'
import {
  getTranscriptionTranscriptionsTranscriptionIdGetOptions,
  listMinutesForTranscriptionTranscriptionTranscriptionIdMinutesGetOptions,
} from '@/lib/client/@tanstack/react-query.gen'
import { FeatureFlags } from '@/lib/feature-flags'
import { useQuery } from '@tanstack/react-query'
import { LoaderCircle } from 'lucide-react'
import { useFeatureFlagEnabled } from 'posthog-js/react'
import { redirect } from 'next/navigation'
import { BannerNotification } from '@/components/banner-notification'
import { useBannerStore } from '@/stores/use-banner-store'
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
  const [draftTabs, setDraftTabs] = useState<
    { id: string; label: string; minuteId: string | null }[]
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
      isTranscriptionProcessing(query.state.data?.status) ? 2000 : false,
    refetchOnWindowFocus: false,
  })

  const { data: documents = [] } = useQuery(
    listMinutesForTranscriptionTranscriptionTranscriptionIdMinutesGetOptions({
      path: { transcription_id: transcriptionId },
    })
  )

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
  const dateTimeLabel = `${date.toLocaleDateString('en-GB')} at ${date.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })}`
  const isProcessing = isTranscriptionProcessing(transcription.status)

  if (isProcessing) {
    return (
      <StatusNotificationPage
        transcription={transcription}
        dateLabel={dateLabel}
        title="Processing"
      >
        Your transcription is being processed. You can close the tab and come
        back later.
      </StatusNotificationPage>
    )
  }

  if (transcription.status == 'failed') {
    return (
      <StatusNotificationPage
        transcription={transcription}
        dateLabel={dateLabel}
        title="Transcription failed"
      >
        Something went wrong with your transcription. You may need to try again.
      </StatusNotificationPage>
    )
  }

  const handleCreateDocument = () => {
    const id = `new-document-${documentCounter.current++}`
    setDraftTabs((prev) => [
      ...prev,
      { id, label: 'New document', minuteId: null },
    ])
    setActiveTab(id)
  }

  const removeDraftTab = (id: string) => {
    setDraftTabs((prev) => prev.filter((tab) => tab.id !== id))
    setActiveTab('transcript')
  }

  const handleMinuteCreated = (id: string, minuteId: string) => {
    setDraftTabs((prev) =>
      prev.map((tab) => (tab.id === id ? { ...tab, minuteId } : tab))
    )
  }

  const handleDocumentCreated = (id: string, templateName: string) => {
    setDraftTabs((prev) =>
      prev.map((tab) => (tab.id === id ? { ...tab, label: templateName } : tab))
    )
  }

  // Persisted document tabs, minus any doc still shown by its in-session draft tab.
  const draftMinuteIds = new Set(
    draftTabs.flatMap((tab) => (tab.minuteId ? [tab.minuteId] : []))
  )
  const documentTabs = documents.filter((doc) => !draftMinuteIds.has(doc.id!))

  return (
    <div className="flex w-full flex-col">
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
        {documentTabs.map((doc) => (
          <GovukTabs.Panel key={doc.id} id={doc.id!} label={doc.template_name}>
            <DocumentTab transcription={transcription} minute={doc} />
          </GovukTabs.Panel>
        ))}
        {draftTabs.map((tab) => (
          <GovukTabs.Panel key={tab.id} id={tab.id} label={tab.label}>
            <NewDocumentTab
              transcription={transcription}
              onCancel={() => removeDraftTab(tab.id)}
              onMinuteCreated={(minuteId) =>
                handleMinuteCreated(tab.id, minuteId)
              }
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
