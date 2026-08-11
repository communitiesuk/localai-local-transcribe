import { SpeakerEditor } from '@/app/transcriptions/[transcriptionId]/TranscriptionTab/SpeakerEditor'
import { SpeakerNamePopover } from '@/app/transcriptions/[transcriptionId]/TranscriptionTab/SpeakerNamePopover'
import { TranscriptionTextArea } from '@/app/transcriptions/[transcriptionId]/TranscriptionTab/TranscriptionTextArea'
import { GovukButton, GovukButtonGroup } from '@/components/govuk'
import CopyButton from '@/components/ui/copy-button'
import {
  useUpdateTranscription,
  useUpdateTranscriptionSpeakers,
} from '@/hooks/use-update-transcription-speakers'
import { DialogueEntry, TranscriptionGetResponse } from '@/lib/client'
import { getRecordingsForTranscriptionTranscriptionsTranscriptionIdRecordingsGetOptions } from '@/lib/client/@tanstack/react-query.gen'
import { downloadTranscriptDoc } from '@/lib/download-word-doc'
import { cn } from '@/lib/utils'
import { useBannerStore } from '@/stores/use-banner-store'
import { useQuery } from '@tanstack/react-query'
import { Play } from 'lucide-react'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { FormProvider, useFieldArray, useForm, useWatch } from 'react-hook-form'

export type DialogueEntryForm = {
  entries: DialogueEntry[]
}

const LINE_EDIT_ERROR =
  'You must save or cancel your line edit to finish editing'

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

const cloneEntries = (entries: DialogueEntry[]) =>
  entries.map((e) => ({ ...e }))

export function TranscriptionTab({
  transcription,
  onLineEditError,
  onEditModeChange,
}: {
  transcription: TranscriptionGetResponse
  onLineEditError: (error: string | null) => void
  onEditModeChange?: (isEditing: boolean) => void
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
      if (originalSpeaker === newSpeaker) return

      const indices = getValues('entries')
        .map((entry, index) => (entry.speaker === originalSpeaker ? index : -1))
        .filter((index) => index >= 0)

      if (!indices.length) return

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
      if (!entry || entry.speaker === newSpeaker) return

      // Capture the original speaker before making any changes, so we can use it in the persist function
      // (entry is captured by the closure, but the speaker property might change before the persist function is called)
      const originalSpeaker = entry.speaker

      await applySpeakerNameChange({
        indices: [index],
        newSpeaker,
        persist: () =>
          updateDialogueEntrySpeaker(index, {
            new_speaker: newSpeaker,
            expected_speaker: originalSpeaker,
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
  const editSnapshotRef = useRef<DialogueEntry[]>([])
  const [time, setTime] = useState(0)

  const [isLineEditMode, setIsLineEditMode] = useState(false)
  const [selectedLineIndex, setSelectedLineIndex] = useState<number | null>(
    null
  )
  const [selectedLineOriginalText, setSelectedLineOriginalText] = useState('')
  const [lineEditInProgress, setLineEditInProgress] = useState(false)

  const { setBanner, clearBanner } = useBannerStore()

  const setError = useCallback(
    (error: string | null) => {
      onLineEditError(error)
    },
    [onLineEditError]
  )

  const handleDownloadTranscript = () =>
    downloadTranscriptDoc(getValues('entries'))

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

  const enterLineEditMode = () => {
    editSnapshotRef.current = cloneEntries(getValues('entries'))
    setIsLineEditMode(true)
    setSelectedLineIndex(0)
    setSelectedLineOriginalText(getValues('entries.0.text' as const) ?? '')
    setLineEditInProgress(false)
    setError(null)
    onEditModeChange?.(true)

    const startTime = getValues('entries.0.start_time' as const)
    if (audioRef.current && startTime != null) {
      audioRef.current.currentTime = startTime
    }
  }

  const selectLineForEdit = (index: number) => {
    if (lineEditInProgress && selectedLineIndex !== index) {
      setError(LINE_EDIT_ERROR)
      return
    }

    setError(null)
    setSelectedLineIndex(index)
    setSelectedLineOriginalText(
      getValues(`entries.${index}.text` as const) ?? ''
    )

    const startTime = getValues(`entries.${index}.start_time` as const)
    if (audioRef.current && startTime != null) {
      audioRef.current.currentTime = startTime
    }
  }

  const saveLineEdit = async () => {
    if (selectedLineIndex == null) return
    const newText =
      getValues(`entries.${selectedLineIndex}.text` as const) ?? ''
    try {
      await handleUpdateEntryText(
        selectedLineIndex,
        newText,
        selectedLineOriginalText
      )
      editSnapshotRef.current[selectedLineIndex] = {
        ...editSnapshotRef.current[selectedLineIndex],
        text: newText,
      }
      setBanner({
        variant: 'success',
        title: 'Success',
        message: 'Line edit saved',
      })
      setSelectedLineIndex(null)
      setSelectedLineOriginalText('')
      setLineEditInProgress(false)
      setError(null)
    } catch {
      // Error is handled in handleUpdateEntryText but a visual banner
      //isn't provided to relay to the user. Issue raised with the UCD team.
    }
  }

  const cancelLineEdit = () => {
    if (selectedLineIndex != null) {
      setValue(
        `entries.${selectedLineIndex}.text` as const,
        editSnapshotRef.current[selectedLineIndex]?.text ?? '',
        { shouldDirty: false }
      )
    }
    setSelectedLineIndex(null)
    setSelectedLineOriginalText('')
    setLineEditInProgress(false)
    setError(null)
    clearBanner()
  }

  const handleTextInput = useCallback(() => {
    setLineEditInProgress(true)
  }, [])

  const finishEditing = () => {
    if (lineEditInProgress) {
      setError(LINE_EDIT_ERROR)
      return
    }

    setIsLineEditMode(false)
    setSelectedLineIndex(null)
    setSelectedLineOriginalText('')
    setLineEditInProgress(false)
    setError(null)
    clearBanner()
    onEditModeChange?.(false)
  }

  return (
    <div>
      <FormProvider {...methods}>
        <form>
          <GovukButtonGroup className="govuk-!-margin-bottom-4">
            <SpeakerEditor
              src={hasRecordings ? recordings[0].url : undefined}
              onSaveSpeaker={handleRenameSpeakerEverywhere}
              disabled={isLineEditMode}
            />

            <GovukButton
              type="button"
              variant="secondary"
              className="govuk-!-margin-bottom-0"
              onClick={enterLineEditMode}
              disabled={isLineEditMode}
              aria-pressed={isLineEditMode}
            >
              Edit transcript
            </GovukButton>

            <CopyButton
              textToCopy={transcriptionString}
              posthogEvent="transcript_content_copied"
              label="Copy transcript"
              disabled={isLineEditMode}
            />

            {fields.length > 0 && (
              <GovukButton
                type="button"
                variant="secondary"
                className="govuk-!-margin-bottom-0"

                onClick={handleDownloadTranscript}
                disabled={isLineEditMode}
              >
                Download transcript
              </GovukButton>
            )}
          </GovukButtonGroup>

          {hasRecordings && (
            <div className="govuk-!-margin-bottom-2 sticky top-0 bg-[var(--govuk-body-background-colour)] py-2">
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
            </div>
          )}

          {isLineEditMode && (
            <GovukButtonGroup
              className="govuk-!-margin-bottom-4 [scroll-margin-top:5rem]"
              id="line-edit-actions"
            >
              <GovukButton
                type="button"
                variant="primary"
                onClick={saveLineEdit}
                disabled={!lineEditInProgress || selectedLineIndex == null}
              >
                Save line edit
              </GovukButton>
              <GovukButton
                type="button"
                variant="warning"
                onClick={cancelLineEdit}
                disabled={!lineEditInProgress}
              >
                Cancel line edit
              </GovukButton>
              <GovukButton
                type="button"
                onClick={finishEditing}
                variant="secondary"
              >
                Finish editing
              </GovukButton>
            </GovukButtonGroup>
          )}

          <hr className="govuk-section-break govuk-section-break--m govuk-section-break--visible" />

          <div className="flex flex-col gap-6">
            {fields.map((field, index) => {
              const entry = watchedEntries?.[index] ?? field
              const isPlaying = isEntryPlaying(
                time,
                entry.start_time,
                watchedEntries?.[index + 1]?.start_time
              )
              const isSelectedForEdit = selectedLineIndex === index

              return (
                <div
                  className={cn('flex items-start gap-2', {
                    'bg-[var(--govuk-surface-background-colour)]': isPlaying,
                  })}
                  key={field.id}
                  ref={isPlaying ? playingRef : null}
                >
                  {hasRecordings && !isLineEditMode && (
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
                      className="govuk-!-margin-top-1 flex shrink-0 items-center text-[var(--govuk-text-colour)] hover:text-[var(--govuk-link-colour)] focus:bg-[var(--govuk-focus-colour)] focus:text-[var(--govuk-focus-text-colour)] focus:shadow-[0_2px_0_var(--govuk-focus-text-colour)] focus:[outline:3px_solid_transparent]"
                    >
                      <Play size={12} fill="currentColor" aria-hidden="true" />
                    </button>
                  )}

                  {isLineEditMode && (
                    <input
                      type="radio"
                      id={`line-edit-${field.id}`}
                      name="line-edit-selector"
                      checked={isSelectedForEdit}
                      onChange={() => selectLineForEdit(index)}
                      aria-label={`Select line ${index + 1} to edit`}
                      className="mt-1.5 shrink-0 cursor-pointer"
                    />
                  )}

                  <SpeakerNamePopover
                    entry={entry}
                    index={index}
                    onUpdateAll={handleRenameSpeakerEverywhere}
                    onUpdateSingle={handleRenameSingleSpeaker}
                    editing={isLineEditMode}
                  />
                  <TranscriptionTextArea
                    control={control}
                    index={index}
                    onSaveText={handleUpdateEntryText}
                    editing={isLineEditMode ? isSelectedForEdit : false}
                    lineEditMode={isLineEditMode}
                    onTextInput={handleTextInput}
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
