import { GovukButton } from '@/components/govuk'
import { Dispatch, SetStateAction } from 'react'

export const DiscardConfirmDialog = ({
  open,
  setOpen,
  onClickConfirm,
}: {
  open: boolean
  setOpen: Dispatch<SetStateAction<boolean>>
  onClickConfirm: () => void
}) => {
  if (!open) return null

  return (
    <div className="govuk-inset-text">
      <p className="govuk-body">
        Are you sure you want to discard your recording? Your recording has not
        been uploaded yet. Discarding it will delete the recording permanently.
      </p>
      <div className="flex gap-2">
        <GovukButton type="button" onClick={onClickConfirm} variant="warning">
          Discard recording
        </GovukButton>
        <GovukButton
          type="button"
          onClick={() => setOpen(false)}
          variant="secondary"
        >
          Cancel
        </GovukButton>
      </div>
    </div>
  )
}
