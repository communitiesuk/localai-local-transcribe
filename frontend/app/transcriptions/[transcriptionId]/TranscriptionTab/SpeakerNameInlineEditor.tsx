import { DialogueEntryForm } from '@/app/transcriptions/[transcriptionId]/TranscriptionTab/TranscriptionTab'
import { InLineEditForm } from '@/components/govuk/inline-edit-form'
import { GovukModalDialogue } from '@/components/govuk/modal-dialogue'
import { GovukNotificationBanner } from '@/components/govuk/notification-banner'
import { EditSpeakerIcon } from '@/components/icons/edit-speaker-icon'
import { useBannerStore } from '@/stores/use-banner-store'
import posthog from 'posthog-js'
import { useCallback, useState } from 'react'

export const SpeakerNameInlineEditor = ({
  entry,
  index,
  onUpdateAll,
  onUpdateSingle,
  editing,
  onOpen,
}: {
  entry: DialogueEntryForm['entries'][0]
  index: number
  onUpdateAll: (originalSpeaker: string, newName: string) => Promise<void>
  onUpdateSingle: (index: number, newName: string) => Promise<void>
  editing: boolean
  onOpen?: () => void
}) => {
  const { setBanner } = useBannerStore()
  const [open, setOpen] = useState(false)
  const [draftName, setDraftName] = useState(entry.speaker)
  const [isSaving, setIsSaving] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const openModal = () => {
    onOpen?.()
    setDraftName(entry.speaker)
    setErrorMessage(null)
    setOpen(true)
  }

  const requestClose = () => {
    setErrorMessage(null)
    setOpen(false)
  }

  const handleUpdateAll = useCallback(
    async (newName: string) => {
      setIsSaving(true)
      setErrorMessage(null)
      try {
        await onUpdateAll(entry.speaker, newName)
        setOpen(false)
        setErrorMessage(null)
        setBanner({
          message: 'Speaker names updated',
          variant: 'success',
          title: 'Success',
        })
        posthog.capture('speaker_name_edited_in_transcript', {
          update_type: 'all_occurrences',
        })
      } catch {
        setErrorMessage(
          `One or more speaker names could not be updated, please try again.`
        )
      } finally {
        setIsSaving(false)
      }
    },
    [entry.speaker, onUpdateAll, setBanner]
  )

  const handleUpdateSingle = useCallback(
    async (newName: string) => {
      setIsSaving(true)
      setErrorMessage(null)
      try {
        await onUpdateSingle(index, newName)
        setOpen(false)
        setErrorMessage(null)
        setBanner({
          message: 'Speaker name updated',
          variant: 'success',
          title: 'Success',
        })
        posthog.capture('speaker_name_edited_in_transcript', {
          update_type: 'single_occurrence',
          entry_index: index,
        })
      } catch {
        setErrorMessage(
          `One or more speaker names could not be updated, please try again.`
        )
      } finally {
        setIsSaving(false)
      }
    },
    [index, onUpdateSingle, setBanner]
  )

  if (editing) {
    return (
      <span className="govuk-!-font-weight-bold max-w-[200px] min-w-[100px] break-words">
        {entry.speaker}:
      </span>
    )
  }

  return (
    <>
      <span className="flex items-center gap-1">
        <button
          type="button"
          aria-label={`Edit speaker name ${entry.speaker}`}
          className="flex shrink-0 cursor-pointer items-center text-[var(--govuk-text-colour)] hover:text-[var(--govuk-link-colour)]"
          onClick={openModal}
        >
          <EditSpeakerIcon width={16} height={18} />
        </button>
        <span className="govuk-!-font-weight-bold max-w-[200px] min-w-[100px] break-words">
          {entry.speaker}:
        </span>
      </span>
      <GovukModalDialogue
        open={open}
        onClose={requestClose}
        title={`Edit '${entry.speaker}'`}
      >
        {errorMessage && (
          <GovukNotificationBanner title="Error" variant="important">
            <p className="govuk-notification-banner__heading">{errorMessage}</p>
          </GovukNotificationBanner>
        )}
        <InLineEditForm
          key={entry.speaker}
          name={entry.speaker}
          value={draftName}
          onValueChange={setDraftName}
          onUpdate={handleUpdateAll}
          onCancel={requestClose}
          secondaryUpdate={{
            label: 'Update this occurrence',
            onUpdate: handleUpdateSingle,
          }}
          disabled={isSaving}
        />
      </GovukModalDialogue>
    </>
  )
}
