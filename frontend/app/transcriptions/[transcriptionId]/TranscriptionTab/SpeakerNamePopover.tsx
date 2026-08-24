import { DialogueEntryForm } from '@/app/transcriptions/[transcriptionId]/TranscriptionTab/TranscriptionTab'
import { EditSpeakerIcon } from '@/components/icons/edit-speaker-icon'
import { GovukButton, GovukInput } from '@/components/govuk'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import posthog from 'posthog-js'
import { useCallback, useId, useState } from 'react'

export const SpeakerNamePopover = ({
  entry,
  index,
  onUpdateAll,
  onUpdateSingle,
  editing,
}: {
  entry: DialogueEntryForm['entries'][0]
  index: number
  onUpdateAll: (originalSpeaker: string, newName: string) => Promise<void>
  onUpdateSingle: (index: number, newName: string) => Promise<void>
  editing: boolean
}) => {
  const [open, setOpen] = useState(false)
  const [newName, setNewName] = useState(entry.speaker)
  const [isSaving, setIsSaving] = useState(false)
  const inputId = useId()

  const handleUpdateAll = useCallback(async () => {
    setIsSaving(true)
    try {
      await onUpdateAll(entry.speaker, newName)
      setOpen(false)
      posthog.capture('speaker_name_edited_in_transcript', {
        update_type: 'all_occurances',
      })
    } finally {
      setIsSaving(false)
    }
  }, [entry.speaker, newName, onUpdateAll])

  const handleUpdateSingle = useCallback(
    (index: number) => async () => {
      setIsSaving(true)
      try {
        await onUpdateSingle(index, newName)
        setOpen(false)
        posthog.capture('speaker_name_edited_in_transcript', {
          update_type: 'single_occurrence',
          entry_index: index,
        })
      } finally {
        setIsSaving(false)
      }
    },
    [newName, onUpdateSingle]
  )
  const handleOpenChange = (open: boolean) => {
    setOpen(open)

    if (open) {
      setNewName(entry.speaker)
    }
  }

  if (editing) {
    return (
      <span className="govuk-!-font-weight-bold max-w-[200px] min-w-[100px] break-words">
        {entry.speaker}:
      </span>
    )
  }

  return (
    <span className="flex items-center gap-1">
      <Popover open={open} onOpenChange={handleOpenChange}>
        <PopoverTrigger asChild>
          <button
            type="button"
            aria-label={`Edit speaker name ${entry.speaker}`}
            className="flex shrink-0 cursor-pointer items-center text-[var(--govuk-text-colour)] hover:text-[var(--govuk-link-colour)]"
          >
            <EditSpeakerIcon width={16} height={18} />
          </button>
        </PopoverTrigger>
        <PopoverContent className="w-80">
          <div className="grid gap-4">
            <div>
              <h4 className="govuk-heading-s govuk-!-margin-bottom-1">
                Edit speaker name
              </h4>
              <label
                className="govuk-hint govuk-!-margin-bottom-2"
                htmlFor={inputId}
              >
                Update either this occurrence or all occurrences of &apos;
                {entry.speaker}&apos;:
              </label>
            </div>
            <div className="grid gap-2">
              <GovukInput
                id={inputId}
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
              />
              <div className="flex flex-col items-start">
                <GovukButton
                  type="button"
                  variant="secondary"
                  onClick={handleUpdateSingle(index)}
                  disabled={isSaving}
                >
                  Update this occurrence
                </GovukButton>
                <GovukButton
                  type="button"
                  className="govuk-!-margin-bottom-0"
                  onClick={handleUpdateAll}
                  disabled={isSaving}
                >
                  Update all occurrences
                </GovukButton>
              </div>
            </div>
          </div>
        </PopoverContent>
      </Popover>
      <span className="govuk-!-font-weight-bold max-w-[200px] min-w-[100px] break-words">
        {entry.speaker}:
      </span>
    </span>
  )
}
