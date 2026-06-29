import { TranscriptionForm } from '@/components/audio/types'
import { TemplateSelect } from '@/components/template-select/template-select'
import { GovukButton, GovukTextarea } from '@/components/govuk'
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
    <div className="govuk-!-margin-top-4 flex flex-col gap-2">
      <GovukButton
        type="submit"
        disabled={
          isPending ||
          !isShowing ||
          !selectedTemplate ||
          (selectedTemplate.agenda_usage == 'required' && !form.watch('agenda'))
        }
      >
        {isPending ? (
          <span className="flex items-center gap-2">
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
            Uploading
          </span>
        ) : (
          'Upload'
        )}
      </GovukButton>
      <Controller
        control={form.control}
        name="template"
        render={({ field: { value, onChange } }) => (
          <TemplateSelect value={value} onChange={onChange} />
        )}
      />
      {selectedTemplate.agenda_usage != 'not_used' && (
        <div className="govuk-form-group">
          <label className="govuk-label" htmlFor="agenda">
            Agenda (
            {selectedTemplate.agenda_usage == 'optional'
              ? 'optional'
              : 'required'}
            )
          </label>
          <div id="agenda-hint" className="govuk-hint">
            Add discussion points from the meeting that should be included in
            the summary.
          </div>
          <GovukTextarea
            id="agenda"
            aria-describedby="agenda-hint"
            placeholder={`Agenda item 1
Agenda item 2
Agenda item 3
...`}
            {...form.register('agenda', {
              required: selectedTemplate.agenda_usage == 'required',
            })}
          />
        </div>
      )}
    </div>
  )
}
