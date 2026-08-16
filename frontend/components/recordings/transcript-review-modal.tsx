'use client'

import {
  GovukButton,
  GovukModalDialogue,
  GovukModalDialogueActions,
} from '@/components/govuk'
import { useId, useState } from 'react'

interface TranscriptReviewModalProps {
  open: boolean
  onClose: () => void
  onConfirm: () => void
  titleId: string
}

export function TranscriptReviewModal({
  open,
  onClose,
  onConfirm,
  titleId,
}: TranscriptReviewModalProps) {
  const [reviewed, setReviewed] = useState(false)
  const checkboxId = useId()

  const handleClose = () => {
    setReviewed(false)
    onClose()
  }

  const handleConfirm = () => {
    setReviewed(false)
    onConfirm()
  }

  return (
    <GovukModalDialogue
      open={open}
      onClose={handleClose}
      title="Confirm review"
      titleId={titleId}
    >
      <div className="govuk-warning-text govuk-!-margin-bottom-4">
        <span className="govuk-warning-text__icon" aria-hidden="true">
          !
        </span>
        <strong className="govuk-warning-text__text">
          <span className="govuk-visually-hidden">Warning</span>
          AI transcription is not 100% accurate. Human review is always
          necessary.
        </strong>
      </div>

      <p className="govuk-body govuk-!-margin-bottom-4">
        You must confirm that you&apos;ve reviewed the transcript before you
        copy or download it.
      </p>

      <div className="govuk-form-group govuk-!-margin-bottom-4">
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
              I&apos;ve reviewed the transcript
            </label>
          </div>
        </div>
      </div>

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
