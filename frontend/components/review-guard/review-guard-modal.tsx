'use client'

import {
  GovukButton,
  GovukModalDialogue,
  GovukModalDialogueActions,
  GovukWarningText,
  GovukBody,
  GovukFormGroup,
} from '@/components/govuk'
import { useId, useState } from 'react'

interface ReviewGuardModalProps {
  open: boolean
  onClose: () => void
  onConfirm: () => void | Promise<void>
  action: 'copy' | 'download'
  subject: 'transcript' | 'document'
}

export function ReviewGuardModal({
  onClose,
  onConfirm,
  open,
  action,
  subject,
}: ReviewGuardModalProps) {
  const [reviewed, setReviewed] = useState(false)
  const checkboxId = useId()

  const handleClose = () => {
    setReviewed(false)
    onClose()
  }

  const handleConfirm = async () => {
    setReviewed(false)
    await onConfirm()
  }

  return (
    <GovukModalDialogue
      open={open}
      onClose={handleClose}
      title="Confirm review"
      titleId={`${action}-${subject}-modal-title`}
    >
      <GovukWarningText>
        AI {subject === 'transcript' ? 'transcription' : 'summarisation'} is not
        100% accurate. Human review is always necessary.
      </GovukWarningText>

      <GovukBody>
        You must confirm that you&apos;ve reviewed the {subject} before you copy
        or download it.
      </GovukBody>

      <GovukFormGroup>
        <div className="govuk-checkboxes govuk-checkboxes--small">
          <div className="govuk-checkboxes__item">
            <input
              className="govuk-checkboxes__input"
              id={checkboxId}
              type="checkbox"
              checked={reviewed}
              onChange={(e) => setReviewed(e.target.checked)}
            />
            <label
              className="govuk-label govuk-checkboxes__label"
              htmlFor={checkboxId}
            >
              I&apos;ve reviewed the {subject}
            </label>
          </div>
        </div>
      </GovukFormGroup>

      <GovukModalDialogueActions>
        <GovukButton
          type="button"
          onClick={handleConfirm}
          disabled={!reviewed}
          className="govuk-!-margin-bottom-0"
        >
          Confirm
        </GovukButton>

        <GovukButton type="button" variant="link" onClick={handleClose}>
          Cancel
        </GovukButton>
      </GovukModalDialogueActions>
    </GovukModalDialogue>
  )
}
