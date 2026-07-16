import { TranscriptionForm } from '@/components/audio/types'
import { TemplateSelect } from '@/components/template-select/template-select'
import {
  GovukButton,
  GovukCharacterCount,
  GovukFormGroup,
  GovukHint,
  GovukLabel,
  GovukTextarea,
} from '@/components/govuk'
import { MAX_AGENDA_LENGTH } from '@/lib/constants'
import { cn } from '@/lib/utils'
import { Loader2 } from 'lucide-react'
import { Controller, useFormContext } from 'react-hook-form'

export const StartTranscriptionSection = ({
  isShowing,
  isPending,
}: {
  isShowing: boolean
  isPending: boolean
}) => {
  const form = useFormContext<TranscriptionForm>()
  const selectedTemplate = form.watch('template')
  const agendaError = form.formState.errors.agenda

  if (!isShowing) {
    return null
  }
  return (
    <div className="govuk-!-margin-top-4">
      <h2 className="govuk-heading-m">Choose a template</h2>
      <GovukHint className="govuk-!-margin-bottom-4">
        Choose a template style for your meeting summary
      </GovukHint>
      <Controller
        control={form.control}
        name="template"
        render={({ field: { value, onChange } }) => (
          <TemplateSelect value={value} onChange={onChange} />
        )}
      />
      {selectedTemplate?.agenda_usage != 'not_used' && (
        <GovukCharacterCount
          id="agenda"
          maxLength={MAX_AGENDA_LENGTH}
          className="govuk-!-margin-top-4"
        >
          <GovukFormGroup hasError={!!agendaError}>
            <GovukLabel htmlFor="agenda">
              Agenda (
              {selectedTemplate?.agenda_usage == 'optional'
                ? 'optional'
                : 'required'}
              )
            </GovukLabel>
            <GovukHint id="agenda-hint">
              Add discussion points from the meeting that should be included in
              the summary.
            </GovukHint>
            {agendaError && (
              <p id="agenda-error" className="govuk-error-message">
                <span className="govuk-visually-hidden">Error:</span>{' '}
                {agendaError.message}
              </p>
            )}
            <GovukTextarea
              id="agenda"
              className="govuk-js-character-count"
              rows={5}
              aria-invalid={!!agendaError}
              aria-describedby={cn(
                'agenda-info agenda-hint',
                agendaError && 'agenda-error'
              )}
              {...form.register('agenda', {
                required: selectedTemplate?.agenda_usage == 'required',
                maxLength: {
                  value: MAX_AGENDA_LENGTH,
                  message: `Agenda must be ${MAX_AGENDA_LENGTH} characters or less`,
                },
              })}
            />
          </GovukFormGroup>
        </GovukCharacterCount>
      )}
      <GovukButton
        type="submit"
        disabled={
          isPending ||
          !isShowing ||
          !selectedTemplate ||
          (selectedTemplate.agenda_usage == 'required' && !form.watch('agenda'))
        }
        className="govuk-!-margin-top-4"
      >
        {isPending ? (
          <>
            <Loader2 className="animate-spin" aria-hidden="true" />
            Uploading
          </>
        ) : (
          'Upload'
        )}
      </GovukButton>
    </div>
  )
}
