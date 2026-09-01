'use client'

import { useEffect, useState } from 'react'
import {
  GovukButton,
  GovukButtonGroup,
  GovukDateInput,
  GovukDetails,
  GovukFormGroup,
  GovukHeading,
  GovukInput,
  GovukLabel,
} from '@/components/govuk'
import type { ErrorItem } from '@/components/govuk/error-summary'
import { TranscriptionGetResponse } from '@/lib/client'
import {
  getTranscriptionTranscriptionsTranscriptionIdGetQueryKey,
  updateTranscriptionMetadataTranscriptionsTranscriptionIdDetailsPutMutation,
} from '@/lib/client/@tanstack/react-query.gen'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { TranscriptionDetailsData } from '@/types/transcriptions'
import { FormProvider, useForm } from 'react-hook-form'
import { useBannerStore } from '@/stores/use-banner-store'
import { useTranscriptionDetailsDraftStore } from '@/stores/use-transcription-details-draft-store'

const TIME_HH_MM_REGEX = /^([01]\d|2[0-3]):[0-5]\d$/

const recordingDetailsErrorMessageMappings = [
  {
    prefix: 'The date recorded must include',
    text: 'Recording date must include a day, month and year',
  },
  {
    prefix: 'The date recorded must be between',
    text: 'The recording date cannot be in the future',
  },
  {
    prefix: 'The date recorded must be today or in the past',
    text: 'The recording date cannot be in the future',
  },
  {
    prefix: 'The date recorded must be a real date',
    text: 'Recording date must be a real date',
  },
  {
    prefix: "The client's date of birth must include",
    text: 'Date of birth must include a day, month and year',
  },
  {
    prefix: "The client's date of birth must be between",
    text: 'Date of birth must be a real date',
  },
  {
    prefix: "The client's date of birth must be today or in the past",
    text: 'Date of birth must be a real date',
  },
  {
    prefix: "The client's date of birth must be a real date",
    text: 'Date of birth must be a real date',
  },
]

const recordingDetailsErrorSummaryText = (message: string): string =>
  recordingDetailsErrorMessageMappings.find(({ prefix }) =>
    message.startsWith(prefix)
  )?.text ?? message

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
  const time = TIME_HH_MM_REGEX.test(timeValue)
    ? `${timeValue}:00`
    : existingTime

  return `${dateValue.year.padStart(4, '0')}-${dateValue.month.padStart(2, '0')}-${dateValue.day.padStart(2, '0')}T${time}`
}

export const RecordingDetails = ({
  dateTimeLabel,
  defaultOpen = false,
  mode = 'panel',
  onErrorListChange,
  transcription,
  onStandaloneComplete,
}: {
  dateTimeLabel: string
  defaultOpen?: boolean
  mode?: 'panel' | 'standalone'
  onErrorListChange: (errors: ErrorItem[]) => void
  transcription: TranscriptionGetResponse
  /**
   * Called when the standalone "add details" step is done - either the
   * details were saved, or the user chose to skip. The caller owns what
   * happens next (e.g. redirecting away, showing a processing spinner).
   */
  onStandaloneComplete?: () => void
}) => {
  const { draft, setDraft, clearDraft } = useTranscriptionDetailsDraftStore()
  const [open, setOpen] = useState(
    draft?.transcriptionId === transcription.id ? draft.isOpen : defaultOpen
  )
  const router = useRouter()
  const isUpload = transcription.is_upload === true
  const isStandalone = mode === 'standalone'

  let clientDateOfBirth: Date | null = null
  if (transcription.client_date_of_birth) {
    clientDateOfBirth = new Date(transcription.client_date_of_birth)
  }

  const form = useForm<TranscriptionDetailsData>({
    mode: 'onSubmit',
    reValidateMode: 'onSubmit',
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
  useEffect(() => {
    if (draft?.transcriptionId === transcription.id) {
      form.reset(draft.data, { keepDefaultValues: true })
    }
  }, [draft, transcription.id, form])

  const { dirtyFields, errors, isSubmitted } = form.formState
  const dateOfRecordingMessage = errors.dateOfRecording?.message
  const dateOfRecordingTimeMessage = errors.dateOfRecordingTime?.message
  const clientDateOfBirthMessage = errors.clientDateOfBirth?.message

  const shouldShowErrorSummary =
    isSubmitted &&
    (!!dateOfRecordingMessage ||
      !!dateOfRecordingTimeMessage ||
      !!clientDateOfBirthMessage)

  useEffect(() => {
    const errorList = [
      typeof dateOfRecordingMessage === 'string' && {
        href: '#date-recorded-day',
        text: recordingDetailsErrorSummaryText(dateOfRecordingMessage),
      },
      typeof dateOfRecordingTimeMessage === 'string' && {
        href: '#time-recorded',
        text: dateOfRecordingTimeMessage,
      },
      typeof clientDateOfBirthMessage === 'string' && {
        href: '#client-dob-day',
        text: recordingDetailsErrorSummaryText(clientDateOfBirthMessage),
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
      if (isStandalone) {
        onStandaloneComplete?.()
      }
    },
    onError: () => {
      setBanner({
        variant: 'important',
        title: 'There is a problem',
        message: 'Failed to update recording details, please try again.',
      })
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
  const detailsForm = (
    <>
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
                  if (!TIME_HH_MM_REGEX.test(value)) {
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
          <p className="govuk-body govuk-!-margin-bottom-1">
            Date recorded{isStandalone ? '' : ':'}
          </p>
          <p className="govuk-body govuk-!-font-weight-bold">{dateTimeLabel}</p>
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
              variant={isStandalone ? 'primary' : 'secondary'}
              className="govuk-!-margin-bottom-2"
              disabled={!isStandalone && !form.formState.isDirty}
            >
              {isStandalone ? 'Add details' : 'Update details'}
            </GovukButton>
            {isStandalone ? (
              <button
                type="button"
                onClick={onStandaloneComplete}
                className="govuk-link govuk-!-margin-bottom-2 bg-transparent p-0"
              >
                Skip step
              </button>
            ) : (
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
            )}
          </GovukButtonGroup>
        </form>
      </FormProvider>
    </>
  )

  if (isStandalone) {
    return (
      <>
        <GovukHeading as="h1" size="xl">
          Add details
        </GovukHeading>
        <p className="govuk-body">
          Enter some details to help you find the recording later
        </p>
        {detailsForm}
      </>
    )
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
        {detailsForm}
      </GovukDetails>
    </>
  )
}
