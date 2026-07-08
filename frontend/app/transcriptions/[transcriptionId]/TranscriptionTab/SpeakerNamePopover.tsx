import { DialogueEntryForm } from '@/app/transcriptions/[transcriptionId]/TranscriptionTab/TranscriptionTab'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import { PenIcon } from 'lucide-react'
import posthog from 'posthog-js'
import { useCallback, useEffect, useState } from 'react'

export const SpeakerNamePopover = ({
  entry,
  index,
  onUpdateAll,
  onUpdateSingle,
}: {
  entry: DialogueEntryForm['entries'][0]
  index: number
  onUpdateAll: (originalSpeaker: string, newName: string) => Promise<void>
  onUpdateSingle: (index: number, newName: string) => Promise<void>
}) => {
  const [open, setOpen] = useState(false)
  const [newName, setNewName] = useState(entry.speaker)
  const [isSaving, setIsSaving] = useState(false)

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
  return (
    <Popover open={open} onOpenChange={(open) => setOpen(open)}>
      <PopoverTrigger asChild>
        <div
          className="group flex max-w-[200px] min-w-[100px] cursor-pointer items-start space-x-1"
          onClick={() => setOpen(true)}
        >
          <PenIcon className="mt-1 size-4 shrink-0 text-gray-400 transition-colors group-hover:text-blue-500" />
          <span className="font-bold break-words group-hover:text-blue-500">
            {entry.speaker}:
          </span>
        </div>
      </PopoverTrigger>
      <PopoverContent className="w-80">
        <div className="grid gap-4">
          <div className="space-y-2">
            <h4 className="leading-none font-medium">Edit Speaker Name</h4>
            <p className="text-muted-foreground text-sm">
              Update either this occurrence or all occurrences of &apos;
              {entry.speaker}&apos;:
            </p>
          </div>
          <div className="grid gap-2">
            <Input
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              className="col-span-3"
            />
            <div className="">
              <Button
                type="button"
                onClick={handleUpdateSingle(index)}
                variant="outline"
                disabled={isSaving}
              >
                Update this occurrence
              </Button>
              <Button
                type="button"
                className="mt-2"
                onClick={handleUpdateAll}
                disabled={isSaving}
              >
                Update all occurrences
              </Button>
            </div>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  )
}
