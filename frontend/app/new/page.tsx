'use client'

import {
  GovukBackLink,
  GovukButton,
  GovukErrorSummary,
  GovukFieldset,
  GovukFormGroup,
  GovukLegend,
  GovukRadios,
} from '@/components/govuk'
import { useRouter } from 'next/navigation'
import { Controller, useForm } from 'react-hook-form'

type CaptureMethodForm = {
  captureMethod: 'upload' | 'record-virtual' | 'record-audio'
}

const CAPTURE_OPTIONS = [
  {
    value: 'upload' as const,
    label: 'Upload file',
    hint: 'Upload a recording from your computer',
  },
  {
    value: 'record-virtual' as const,
    label: 'Record a virtual meeting',
    hint: 'Record a virtual meeting in another tab',
  },
  {
    value: 'record-audio' as const,
    label: 'Record audio',
    hint: 'Record audio using your microphone',
  },
]

export default function NewTranscriptPage() {
  const router = useRouter()
  const {
    control,
    handleSubmit,
    formState: { errors },
  } = useForm<CaptureMethodForm>()

  const onSubmit = (data: CaptureMethodForm) => {
    router.push(`/new/${data.captureMethod}`)
  }

  return (
    <div className="govuk-grid-row">
      <div className="govuk-grid-column-two-thirds">
        <GovukBackLink href="/" />
        {errors.captureMethod && (
          <GovukErrorSummary
            errorList={[
              {
                href: '#captureMethod',
                text: 'Select how you want to capture audio',
              },
            ]}
          />
        )}
        <form onSubmit={handleSubmit(onSubmit)} noValidate>
          <GovukFormGroup hasError={!!errors.captureMethod}>
            <GovukFieldset
              aria-describedby={
                errors.captureMethod ? 'captureMethod-error' : undefined
              }
            >
              <GovukLegend size="xl">
                <h1 className="govuk-fieldset__heading">
                  How do you want to capture audio?
                </h1>
              </GovukLegend>
              {errors.captureMethod && (
                <p id="captureMethod-error" className="govuk-error-message">
                  <span className="govuk-visually-hidden">Error:</span> Select
                  how you want to capture audio
                </p>
              )}
              <Controller
                control={control}
                name="captureMethod"
                rules={{ required: true }}
                render={({ field: { onChange, value, ref, disabled } }) => (
                  <GovukRadios
                    name="captureMethod"
                    value={value}
                    onChange={onChange}
                    disabled={disabled}
                    ref={ref}
                    options={CAPTURE_OPTIONS}
                  />
                )}
              />
            </GovukFieldset>
          </GovukFormGroup>
          <GovukButton type="submit">Continue</GovukButton>
        </form>
      </div>
    </div>
  )
}
