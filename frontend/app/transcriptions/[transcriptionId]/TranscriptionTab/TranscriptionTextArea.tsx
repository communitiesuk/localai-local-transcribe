import { DialogueEntryForm } from '@/app/transcriptions/[transcriptionId]/TranscriptionTab/TranscriptionTab'
import posthog from 'posthog-js'
import { Control, Controller } from 'react-hook-form'

export const TranscriptionTextArea = ({
  index,
  control,
  onSaveText,
  editing,
  lineEditMode = false,
  onTextInput,
}: {
  index: number
  control: Control<DialogueEntryForm>
  onSaveText: (
    index: number,
    newText: string,
    previousText: string
  ) => Promise<void>
  editing: boolean
  lineEditMode?: boolean
  onTextInput?: () => void
}) => {
  return (
    <div className="flex-1">
      <Controller
        render={({ field }) =>
          editing ? (
            <p
              className="govuk-body govuk-!-margin-bottom-0 flex-1 cursor-text px-2"
              onClick={(e) => {
                const target = e.target as HTMLParagraphElement
                if (target.getAttribute('contenteditable') !== 'true') {
                  target.setAttribute('contenteditable', 'true')
                  target.focus()
                }
              }}
              onInput={() => {
                if (lineEditMode) onTextInput?.()
              }}
              onBlur={(e) => {
                const target = e.target as HTMLParagraphElement
                target.setAttribute('contenteditable', 'false')
                const newText = target.innerText.trim()

                if (lineEditMode) {
                  if (newText !== field.value) {
                    field.onChange(newText)
                  }
                  return
                }

                if (newText !== field.value) {
                  // Rollback is handled in the parent callback; prevent unhandled rejections from blur events.
                  void onSaveText(index, newText, field.value).catch(() => {})

                  posthog.capture('transcript_text_edited', {
                    entry_index: index,
                  })
                }
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  e.currentTarget.blur()
                }
              }}
            >
              {field.value}
            </p>
          ) : (
            <p className="govuk-body govuk-!-margin-bottom-0 flex-1 px-2">
              {field.value}
            </p>
          )
        }
        control={control}
        name={`entries.${index}.text`}
      />
    </div>
  )
}
