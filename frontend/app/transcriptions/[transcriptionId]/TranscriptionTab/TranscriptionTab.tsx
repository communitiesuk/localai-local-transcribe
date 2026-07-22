import { SpeakerEditor } from '@/app/transcriptions/[transcriptionId]/TranscriptionTab/SpeakerEditor'
import { SpeakerNamePopover } from '@/app/transcriptions/[transcriptionId]/TranscriptionTab/SpeakerNamePopover'
import { TranscriptionTextArea } from '@/app/transcriptions/[transcriptionId]/TranscriptionTab/TranscriptionTextArea'
import { DownloadButton } from '@/components/download-button'
import CopyButton from '@/components/ui/copy-button'
import {
  useUpdateTranscription,
  useUpdateTranscriptionSpeakers,
} from '@/hooks/use-update-transcription-speakers'
import { DialogueEntry, TranscriptionGetResponse } from '@/lib/client'
import { getRecordingsForTranscriptionTranscriptionsTranscriptionIdRecordingsGetOptions } from '@/lib/client/@tanstack/react-query.gen'
import { cn } from '@/lib/utils'
import { useQuery } from '@tanstack/react-query'
import { Play } from 'lucide-react'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { FormProvider, useFieldArray, useForm, useWatch } from 'react-hook-form'

export type DialogueEntryForm = {
  entries: DialogueEntry[]
}

export function isEntryPlaying(
  time: number,
  entryStart: number,
  nextEntryStart?: number
): boolean {
  return (
    time >= entryStart &&
    (nextEntryStart === undefined || time < nextEntryStart)
  )
}

export function buildTranscriptionHtml(
  entries: DialogueEntry[] | null | undefined
): string {
  const safeEntries = entries ?? []
  return safeEntries
    .map((entry) => `<p><b>${entry.speaker}:</b> ${entry.text}</p>`)
    .join('\n\n')
}

export function TranscriptionTab({
  transcription,
}: {
  transcription: TranscriptionGetResponse
}) {
  const methods = useForm<DialogueEntryForm>({
    defaultValues: { entries: transcription.dialogue_entries || [] },
    mode: 'onBlur',
  })
  const { control, reset, resetField, setValue, getValues } = methods
  const watchedEntries = useWatch({ control, name: 'entries' })

  const transcriptionString = useMemo(
    () => buildTranscriptionHtml(watchedEntries),
    [watchedEntries]
  )

  useEffect(() => {
    reset({ entries: transcription.dialogue_entries || [] })
  }, [reset, transcription.dialogue_entries])

  const { updateDialogueEntryText } = useUpdateTranscription(transcription.id!)
  const { renameSpeakerEverywhere, updateDialogueEntrySpeaker } =
    useUpdateTranscriptionSpeakers(transcription.id!)

  const { fields } = useFieldArray({ control, name: 'entries' })

  const applySpeakerNameChange = useCallback(
    async ({
      indices,
      newSpeaker,
      persist,
    }: {
      indices: number[]
      newSpeaker: string
      persist: () => Promise<void>
    }) => {
      const previousSpeakers = indices.map((index) => ({
        index,
        speaker: getValues(`entries.${index}.speaker` as const),
      }))

      indices.forEach((index) => {
        setValue(`entries.${index}.speaker` as const, newSpeaker, {
          shouldDirty: true,
        })
      })

      try {
        await persist()
        indices.forEach((index) => {
          resetField(`entries.${index}.speaker` as const, {
            defaultValue: newSpeaker,
          })
        })
      } catch (error) {
        previousSpeakers.forEach(({ index, speaker }) => {
          setValue(`entries.${index}.speaker` as const, speaker, {
            shouldDirty: false,
          })
        })
        throw error
      }
    },
    [getValues, resetField, setValue]
  )

  const handleUpdateEntryText = useCallback(
    async (index: number, newText: string, previousText: string) => {
      const entry = getValues(`entries.${index}` as const)
      if (!entry || previousText === newText) {
        return
      }

      setValue(`entries.${index}.text` as const, newText, {
        shouldDirty: true,
      })

      try {
        await updateDialogueEntryText(index, {
          new_text: newText,
          expected_text: previousText,
          expected_speaker: entry.speaker,
          expected_start_time: entry.start_time,
          expected_end_time: entry.end_time,
        })
        resetField(`entries.${index}.text` as const, {
          defaultValue: newText,
        })
      } catch (error) {
        setValue(`entries.${index}.text` as const, previousText, {
          shouldDirty: false,
        })
        throw error
      }
    },
    [getValues, resetField, setValue, updateDialogueEntryText]
  )

  const handleRenameSpeakerEverywhere = useCallback(
    async (originalSpeaker: string, newSpeaker: string) => {
      if (originalSpeaker === newSpeaker) {
        return
      }

      const indices = getValues('entries')
        .map((entry, index) => (entry.speaker === originalSpeaker ? index : -1))
        .filter((index) => index >= 0)

      if (!indices.length) {
        return
      }

      await applySpeakerNameChange({
        indices,
        newSpeaker,
        persist: () =>
          renameSpeakerEverywhere({
            original_speaker: originalSpeaker,
            new_speaker: newSpeaker,
          }),
      })
    },
    [applySpeakerNameChange, getValues, renameSpeakerEverywhere]
  )

  const handleRenameSingleSpeaker = useCallback(
    async (index: number, newSpeaker: string) => {
      const entry = getValues(`entries.${index}` as const)
      if (!entry || entry.speaker === newSpeaker) {
        return
      }

      await applySpeakerNameChange({
        indices: [index],
        newSpeaker,
        persist: () =>
          updateDialogueEntrySpeaker(index, {
            new_speaker: newSpeaker,
            expected_speaker: entry.speaker,
            expected_start_time: entry.start_time,
            expected_end_time: entry.end_time,
          }),
      })
    },
    [applySpeakerNameChange, getValues, updateDialogueEntrySpeaker]
  )

  const { data: recordings } = useQuery({
    ...getRecordingsForTranscriptionTranscriptionsTranscriptionIdRecordingsGetOptions(
      { path: { transcription_id: transcription.id! } }
    ),
  })

  const audioRef = useRef<HTMLAudioElement | null>(null)
  const playingRef = useRef<HTMLDivElement | null>(null)
  const [time, setTime] = useState(0)

  const scrollToPlaying = () => {
    if (playingRef.current) {
      playingRef.current.scrollIntoView({
        block: 'center',
        behavior: 'smooth',
      })
    }
  }

  const hasRecordings = !!recordings && !!recordings.length

  const delayedScroll = () =>
    new Promise((resolve) => setTimeout(resolve, 100)).then(scrollToPlaying)

  return (
    <div>
      <FormProvider {...methods}>
        <form>
          <div className="flex justify-between">
            <SpeakerEditor
              src={hasRecordings ? recordings[0].url : undefined}
              onSaveSpeaker={handleRenameSpeakerEverywhere}
            />
            <CopyButton
              textToCopy={transcriptionString}
              posthogEvent="transcript_content_copied"
            />
          </div>
          {hasRecordings && (
            <div className="sticky top-0 mb-2 flex flex-col gap-2 rounded border bg-white p-2">
              <audio
                controls
                src={recordings[0].url}
                className="w-full"
                ref={audioRef}
                onSeeked={delayedScroll}
                onTimeUpdate={(e) => {
                  if ((e.target as HTMLAudioElement).currentTime != null) {
                    setTime((e.target as HTMLAudioElement).currentTime)
                  }
                }}
              />
              <div className="flex justify-between">
                <div>
                  <button
                    type="button"
                    onClick={scrollToPlaying}
                    className="govuk-link govuk-body-s"
                  >
                    Scroll to playing
                  </button>
                </div>
                <DownloadButton recordings={recordings} />
              </div>
            </div>
          )}
          <div className="flex flex-col gap-6">
            {fields.map((field, index) => {
              const entry = watchedEntries?.[index] ?? field
              const isPlaying = isEntryPlaying(
                time,
                entry.start_time,
                watchedEntries?.[index + 1]?.start_time
              )
              return (
                <div
                  className={cn('flex items-start gap-2 rounded', {
                    'bg-[var(--govuk-surface-background-colour)]': isPlaying,
                  })}
                  key={field.id}
                  ref={isPlaying ? playingRef : null}
                >
                  {hasRecordings && (
                    <button
                      type="button"
                      aria-label="Play from here"
                      onClick={() => {
                        if (audioRef.current) {
                          audioRef.current.currentTime = entry.start_time
                          if (audioRef.current.paused) {
                            audioRef.current.play()
                          }
                        }
                      }}
                      className="flex size-6 shrink-0 items-center justify-center rounded-full bg-[var(--govuk-link-colour)] text-white hover:bg-[var(--govuk-link-hover-colour)] focus:bg-[var(--govuk-focus-colour)] focus:text-[var(--govuk-focus-text-colour)] focus:shadow-[0_2px_0_var(--govuk-focus-text-colour)] focus:[outline:3px_solid_transparent]"
                    >
                      <Play size={14} aria-hidden="true" />
                    </button>
                  )}
                  <SpeakerNamePopover
                    entry={entry}
                    index={index}
                    onUpdateAll={handleRenameSpeakerEverywhere}
                    onUpdateSingle={handleRenameSingleSpeaker}
                  />
                  <TranscriptionTextArea
                    control={control}
                    index={index}
                    onSaveText={handleUpdateEntryText}
                  />
                </div>
              )
            })}
          </div>
        </form>
      </FormProvider>
    </div>
  )
}
