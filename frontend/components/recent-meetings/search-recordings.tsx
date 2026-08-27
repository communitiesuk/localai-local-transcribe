'use client'

import {
  GovukButton,
  GovukButtonGroup,
  GovukDateInput,
  GovukDetails,
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
import { SearchRecordingsFormData } from '@/types/search-recordings'
import { usePathname, useRouter, useSearchParams } from 'next/navigation'
import { useState } from 'react'
import { useForm, useWatch } from 'react-hook-form'

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

export const SearchRecordings = () => {
  const [open, setOpen] = useState(false)
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
    const params = new URLSearchParams(searchParams)

    setRecordingSearchParams(params, data)
    params.delete('page')
    router.replace(hrefWithParams(pathname, params))
  }

  const handleReset = () => {
    const params = new URLSearchParams(searchParams)

    recordingSearchParamKeys.forEach((key) => params.delete(key))
    params.delete('page')
    form.reset(defaultValues)
    router.replace(hrefWithParams(pathname, params))
  }

  return (
    <>
      <GovukHeading as="h2" size="m" className="govuk-!-margin-bottom-2">
        Search
      </GovukHeading>
      <GovukDetails
        open={open}
        summary={open ? 'Hide search fields' : 'Show search fields'}
        onToggle={(e) => setOpen(e.currentTarget.open)}
      >
        <form onSubmit={form.handleSubmit(handleSubmit)}>
          <GovukDateInput
            legend="Date of recording"
            id="dateOfRecording"
            control={form.control}
            name="dateOfRecording"
            mustBePastOrFuture="past"
            description="date of recording"
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
              Submit
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
