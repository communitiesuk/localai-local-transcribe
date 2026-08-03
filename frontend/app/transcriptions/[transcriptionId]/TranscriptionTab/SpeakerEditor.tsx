'use client'

import { DialogueEntryForm } from '@/app/transcriptions/[transcriptionId]/TranscriptionTab/TranscriptionTab'
import { GovukButton, GovukInput } from '@/components/govuk'
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { DialogueEntry } from '@/lib/client'
import { Pause, Play } from 'lucide-react'
import { useCallback, useEffect, useId, useMemo, useRef, useState } from 'react'
import { FormProvider, useFormContext, useWatch } from 'react-hook-form'

export const SpeakerEditor = ({
  src,
  onSaveSpeaker,
}: {
  src?: string
  onSaveSpeaker: (originalSpeaker: string, newSpeaker: string) => Promise<void>
}) => {
  const form = useFormContext<DialogueEntryForm>()
  const entries = useWatch({ control: form.control, name: 'entries' })

  const speakers = useMemo(() => {
    const speakerMap: Map<string, DialogueEntry[]> = new Map<
      string,
      DialogueEntry[]
    >()
    entries?.forEach((entry) => {
      speakerMap.set(entry.speaker, [
        ...(speakerMap.get(entry.speaker) || []),
        entry,
      ])
    })
    return speakerMap
  }, [entries])

  const [selected, setSelected] = useState<string | undefined>()
  const onSave = useCallback(
    (originalSpeaker: string) => async (newSpeaker: string) => {
      await onSaveSpeaker(originalSpeaker, newSpeaker)
    },
    [onSaveSpeaker]
  )

  return (
    <Dialog>
      <DialogTrigger asChild>
        <GovukButton
          type="button"
          variant="secondary"
          className="govuk-!-margin-bottom-0"
        >
          Edit speaker names
        </GovukButton>
      </DialogTrigger>
      <DialogContent className="scroll max-h-screen overflow-y-auto sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>Edit speaker names</DialogTitle>
          <DialogDescription>
            You can edit speaker names here or on the transcript. Click on the
            speaker&apos;s name to edit
          </DialogDescription>
        </DialogHeader>
        <FormProvider {...form}>
          <form className="flex flex-col gap-2">
            {Array.from(speakers.entries()).map(([speaker, entries]) => (
              <div key={speaker} className="flex w-full justify-between gap-1">
                <SpeakerNameEditor
                  speaker={speaker}
                  onSave={onSave(speaker)}
                  selected={selected == speaker}
                  setSelected={setSelected}
                />
                <div className="flex gap-1">
                  {src &&
                    entries
                      .slice(0, 3)
                      .map((entry) => (
                        <PlayClipButton
                          key={entry.start_time}
                          src={src}
                          startTime={entry.start_time}
                          endTime={entry.end_time}
                        />
                      ))}
                </div>
              </div>
            ))}
          </form>
        </FormProvider>
        <DialogFooter>
          <DialogClose asChild>
            <GovukButton type="button" variant="secondary">
              Done
            </GovukButton>
          </DialogClose>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

const SpeakerNameEditor = ({
  speaker,
  onSave,
  selected,
  setSelected,
}: {
  speaker: string
  onSave: (name: string) => Promise<void>
  selected: boolean
  setSelected: (n: string | undefined) => void
}) => {
  const [value, setValue] = useState(speaker)
  const inputRef = useRef<HTMLInputElement | null>(null)
  const [isSaving, setIsSaving] = useState(false)
  const inputId = useId()

  useEffect(() => {
    if (selected && inputRef.current) {
      inputRef.current.focus()
    }
  }, [selected])

  if (!selected) {
    return (
      <button
        type="button"
        onClick={() => {
          setSelected(speaker)
        }}
        className="govuk-link govuk-body cursor-pointer text-left"
      >
        {speaker}
      </button>
    )
  }

  return (
    <div className="flex flex-1 items-start gap-1">
      <GovukInput
        id={inputId}
        aria-label={`Speaker name for ${speaker}`}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        ref={inputRef}
      />
      <GovukButton
        type="button"
        variant="secondary"
        className="govuk-!-margin-bottom-0"
        disabled={isSaving}
        onClick={() => {
          setValue(speaker)
          setSelected(undefined)
        }}
      >
        Cancel
      </GovukButton>
      <GovukButton
        type="button"
        className="govuk-!-margin-bottom-0"
        disabled={isSaving}
        onClick={async () => {
          setIsSaving(true)
          try {
            await onSave(value)
            setSelected(undefined)
          } finally {
            setIsSaving(false)
          }
        }}
      >
        Save
      </GovukButton>
    </div>
  )
}

const PlayClipButton = ({
  src,
  startTime,
  endTime,
}: {
  src: string
  startTime: number
  endTime: number
}) => {
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const [isPlaying, setPlaying] = useState(false)
  useEffect(() => {
    if (!audioRef.current) {
      audioRef.current = new Audio(src)
    }
    const audio = audioRef.current
    audio.currentTime = startTime
    const onPlay = () => {
      audio.currentTime = startTime
      setPlaying(true)
    }
    const onPause = () => {
      setPlaying(false)
    }
    const onTimeUpdate = () => {
      const current = audio.currentTime

      // Stop playback when we reach the end time
      if (current >= endTime) {
        audio.pause()
      }
    }
    audio.addEventListener('play', onPlay)
    audio.addEventListener('pause', onPause)
    audio.addEventListener('timeupdate', onTimeUpdate)
    return () => {
      audio.pause()
      audio.removeEventListener('play', onPlay)
      audio.removeEventListener('pause', onPause)
      audio.removeEventListener('timeupdate', onTimeUpdate)
    }
  }, [endTime, src, startTime])

  return (
    <button
      type="button"
      aria-label={isPlaying ? 'Pause clip' : 'Play clip'}
      className="flex size-8 shrink-0 items-center justify-center rounded-full bg-[var(--govuk-link-colour)] text-white hover:bg-[var(--govuk-link-hover-colour)] focus:bg-[var(--govuk-focus-colour)] focus:text-[var(--govuk-focus-text-colour)] focus:shadow-[0_2px_0_var(--govuk-focus-text-colour)] focus:[outline:3px_solid_transparent]"
      onClick={() => {
        if (audioRef.current) {
          if (audioRef.current.paused) {
            audioRef.current.play()
          } else {
            audioRef.current.pause()
          }
        }
      }}
    >
      {isPlaying ? (
        <Pause size={14} aria-hidden="true" />
      ) : (
        <Play size={14} aria-hidden="true" />
      )}
    </button>
  )
}
