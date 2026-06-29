import { GovukButton } from '@/components/govuk'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Trash2 } from 'lucide-react'
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
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            Are you sure you want to discard your recording?
          </DialogTitle>
          <DialogDescription>
            Your recording has not been uploaded yet. Discarding it will delete
            the recording permanently.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter className="flex gap-3">
          <GovukButton
            type="button"
            variant="secondary"
            onClick={() => setOpen(false)}
          >
            Cancel
          </GovukButton>
          <GovukButton
            type="button"
            variant="warning"
            onClick={onClickConfirm}
          >
            <Trash2 aria-hidden="true" /> Discard recording
          </GovukButton>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
