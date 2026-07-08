'use client'

import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { useUpdateTranscription } from '@/hooks/use-update-transcription-speakers'
import { TranscriptionMetadata } from '@/lib/client'
import { Loader, Save } from 'lucide-react'
import posthog from 'posthog-js'
import { Dispatch, SetStateAction, useState } from 'react'
import { useForm } from 'react-hook-form'

export const RenameDialog = ({
  open,
  setOpen,
  transcription,
}: {
  open: boolean
  setOpen: Dispatch<SetStateAction<boolean>>
  transcription: TranscriptionMetadata
}) => {
  const { updateTitle } = useUpdateTranscription(transcription.id)
  const [isPending, setIsPending] = useState(false)
  const form = useForm<{ title: string | undefined }>({
    defaultValues: { title: transcription.title ?? undefined },
  })
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent>
        <form
          onSubmit={form.handleSubmit(async ({ title }) => {
            setIsPending(true)
            try {
              await updateTitle(title)
              posthog.capture('edited_transcript_title', {
                transcriptionId: transcription.id,
              })
              setOpen(false)
            } finally {
              setIsPending(false)
            }
          })}
        >
          <DialogHeader>
            <DialogTitle>Rename meeting</DialogTitle>
            <DialogClose />
          </DialogHeader>
          <Input
            {...form.register('title')}
            className="mb-4"
            placeholder="Add title"
          />
          <DialogFooter>
            <DialogClose asChild>
              <Button
                variant="secondary"
                type="button"
                className="hover:bg-slate-200"
              >
                Cancel
              </Button>
            </DialogClose>
            <Button className="active:bg-yellow-400" type="submit">
              {isPending ? (
                <Loader />
              ) : (
                <>
                  <Save /> Save
                </>
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
