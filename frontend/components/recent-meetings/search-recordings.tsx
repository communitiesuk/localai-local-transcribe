'use client'

import {
  GovukButton,
  GovukButtonGroup,
  GovukDateInput,
  GovukDetails,
  GovukErrorSummary,
  GovukFormGroup,
  GovukHeading,
  GovukLabel,
} from '@/components/govuk'
import {
  hrefWithParams,
  recordingSearchParamKeys,
  setRecordingSearchParams,
  valuesFromRecordingSearchParams,
} from '@/components/recent-meetings/search-recording-params'
import type { ErrorItem } from '@/components/govuk/error-summary'
import { SearchRecordingsFormData } from '@/types/search-recordings'
import { usePathname, useRouter, useSearchParams } from 'next/navigation'
import { useState } from 'react'
import { type SubmitErrorHandler, useForm, useWatch } from 'react-hook-form'

const defaultValues: SearchRecordingsFormData = {
  dateOfRecording: { day: '', month: '', year: '' },
  clientName: '',
  caseId: '',
  subject: '',
  clientDateOfBirth: { day: '', month: '', year: '' },
}

const hasAnySearchValue = (values: SearchRecordingsFormData): boolean =>
  Boolean(
    values.clientName.trim() ||
    values.caseId.trim() ||
    values.subject.trim() ||
    values.dateOfRecording.day.trim() ||
    values.dateOfRecording.month.trim() ||
    values.dateOfRecording.year.trim() ||
    values.clientDateOfBirth.day.trim() ||
    values.clientDateOfBirth.month.trim() ||
    values.clientDateOfBirth.year.trim()
  )

const errorMessageMappings = [
  {
    prefix: 'The date of birth must include',
    text: 'Date of birth must include a day, month and year',
  },
  {
    prefix: 'The date of birth must be between',
    text: 'Date of birth must be a real date',
  },
  {
    prefix: 'The date of birth must be a real date',
    text: 'Date of birth must be a real date',
  },
  {
    prefix: 'The Recording date cannot be in the future',
    text: 'The recording date cannot be in the future',
  },
  {
    prefix: 'The Recording date must be today or in the past',
    text: 'The recording date cannot be in the future',
  },
  {
    prefix: 'The Recording date must be a real date',
    text: 'Recording date must be a real date',
  },
]

const errorSummaryText = (message: string): string =>
  errorMessageMappings.find(({ prefix }) => message.startsWith(prefix))?.text ??
  message

export const SearchRecordings = () => {
  const [open, setOpen] = useState(false)
  const [errorList, setErrorList] = useState<ErrorItem[]>([])
  const pathname = usePathname()
  const router = useRouter()
  const searchParams = useSearchParams()

  const form = useForm<SearchRecordingsFormData>({
    defaultValues: valuesFromRecordingSearchParams(searchParams),
  })

  const watchedValues = useWatch({ control: form.control })
  const values: SearchRecordingsFormData = {
    dateOfRecording: {
      ...defaultValues.dateOfRecording,
      ...watchedValues.dateOfRecording,
    },
    clientName: watchedValues.clientName ?? '',
    caseId: watchedValues.caseId ?? '',
    subject: watchedValues.subject ?? '',
    clientDateOfBirth: {
      ...defaultValues.clientDateOfBirth,
      ...watchedValues.clientDateOfBirth,
    },
  }
  const hasSearchValue = hasAnySearchValue(values)

  const handleSubmit = (data: SearchRecordingsFormData) => {
    setErrorList([])

    const params = new URLSearchParams(searchParams)

    setRecordingSearchParams(params, data)
    params.delete('page')
    router.replace(hrefWithParams(pathname, params))
  }

  const handleInvalid: SubmitErrorHandler<SearchRecordingsFormData> = (
    errors
  ) => {
    setErrorList(
      [
        typeof errors.dateOfRecording?.message === 'string' && {
          href: '#dateOfRecording',
          text: errorSummaryText(errors.dateOfRecording.message),
        },
        typeof errors.clientDateOfBirth?.message === 'string' && {
          href: '#clientDateOfBirth',
          text: errorSummaryText(errors.clientDateOfBirth.message),
        },
      ].filter(Boolean) as ErrorItem[]
    )
  }

  const handleReset = () => {
    const params = new URLSearchParams(searchParams)

    recordingSearchParamKeys.forEach((key) => params.delete(key))
    params.delete('page')
    form.reset(defaultValues)
    setErrorList([])
    router.replace(hrefWithParams(pathname, params))
  }

  return (
    <>
      {errorList.length > 0 && (
        <GovukErrorSummary title="There is a problem" errorList={errorList} />
      )}

      <GovukHeading as="h2" size="m" className="govuk-!-margin-bottom-2">
        Search
      </GovukHeading>
      <GovukDetails
        open={open}
        summary={open ? 'Hide search fields' : 'Show search fields'}
        onToggle={(e) => setOpen(e.currentTarget.open)}
      >
        <form onSubmit={form.handleSubmit(handleSubmit, handleInvalid)}>
          <GovukDateInput
            legend="Date of recording"
            id="dateOfRecording"
            control={form.control}
            name="dateOfRecording"
            mustBePastOrFuture="past"
            description="Recording date"
            validationMode="partial-date"
          />
          <GovukFormGroup>
            <GovukLabel htmlFor="clientName">Client name</GovukLabel>
            <input
              id="clientName"
              type="text"
              {...form.register('clientName')}
              className="govuk-input"
            />
          </GovukFormGroup>

          <GovukFormGroup>
            <GovukLabel htmlFor="caseId">Case ID</GovukLabel>
            <input
              id="caseId"
              type="text"
              {...form.register('caseId')}
              className="govuk-input"
            />
          </GovukFormGroup>

          <GovukFormGroup>
            <GovukLabel htmlFor="subject">Subject</GovukLabel>
            <input
              id="subject"
              type="text"
              {...form.register('subject')}
              className="govuk-input"
            />
          </GovukFormGroup>

          <GovukDateInput
            legend="Client date of birth"
            id="clientDateOfBirth"
            control={form.control}
            name="clientDateOfBirth"
            mustBePastOrFuture="past"
            description="date of birth"
          />
          <GovukButtonGroup>
            <GovukButton
              type="submit"
              variant="primary"
              className="govuk-!-margin-bottom-1"
              disabled={!hasSearchValue}
            >
              Search
            </GovukButton>
            <GovukButton
              type="button"
              variant="secondary"
              className="govuk-!-margin-bottom-1"
              disabled={!hasSearchValue}
              onClick={handleReset}
            >
              Reset
            </GovukButton>
          </GovukButtonGroup>
        </form>
      </GovukDetails>
    </>
  )
}
