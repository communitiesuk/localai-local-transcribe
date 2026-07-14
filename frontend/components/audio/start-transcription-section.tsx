import { TranscriptionForm } from '@/components/audio/types'
import { TemplateSelect } from '@/components/template-select/template-select'
import {
  GovukButton,
  GovukFormGroup,
  GovukHint,
  GovukLabel,
  GovukTextarea,
} from '@/components/govuk'
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
        <GovukFormGroup className="govuk-!-margin-top-4">
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
          <GovukTextarea
            id="agenda"
            aria-describedby="agenda-hint"
            rows={5}
            {...form.register('agenda', {
              required: selectedTemplate?.agenda_usage == 'required',
            })}
          />
        </GovukFormGroup>
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
