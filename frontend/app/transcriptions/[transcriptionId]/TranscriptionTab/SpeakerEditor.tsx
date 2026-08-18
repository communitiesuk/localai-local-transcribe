'use client'

import { DialogueEntryForm } from '@/app/transcriptions/[transcriptionId]/TranscriptionTab/TranscriptionTab'
import { GovukButton } from '@/components/govuk'
import {
  GovukModalDialogue,
  GovukModalDialogueActions,
} from '@/components/govuk/modal-dialogue'
import { DialogueEntry } from '@/lib/client'
import {
  useEffect,
  useMemo,
  useRef,
  useState,
  RefObject,
  useCallback,
} from 'react'
import { useFormContext, useWatch } from 'react-hook-form'
import { PlayButton } from '@/components/icons/play-button'
import { PauseButton } from '@/components/icons/pause-button'
import { InLineEditForm } from '@/components/govuk/inline-edit-form'
import { ModalConfirmationInterstitial } from '@/components/govuk/modal-confirmation-interstitial'
import { useBannerStore } from '@/stores/use-banner-store'

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

  const [open, setOpen] = useState(false)
  const closeModal = useCallback(() => {
    setOpen(false)
  }, [])

  return (
    <>
      <GovukButton
        type="button"
        variant="secondary"
        className="govuk-!-margin-bottom-0"
        onClick={() => setOpen(true)}
      >
        Edit speaker names
      </GovukButton>
      <SpeakerEditorModal
        open={open}
        onClose={closeModal}
        speakers={speakers}
        src={src}
        onSaveSpeaker={onSaveSpeaker}
      />
    </>
  )
}

type SpeakerEditorModalProps = {
  open: boolean
  onClose: () => void
  speakers: Map<string, DialogueEntry[]>
  src?: string
  onSaveSpeaker: (originalSpeaker: string, newSpeaker: string) => Promise<void>
}

const SpeakerEditorModal = ({
  open,
  onClose,
  speakers,
  src,
  onSaveSpeaker,
}: SpeakerEditorModalProps) => {
  const { setBanner } = useBannerStore()

  const [view, setView] = useState<'list' | 'edit' | 'confirm-discard'>('list')
  const [editingSpeaker, setEditingSpeaker] = useState<string | undefined>()
  const [editInitialValue, setEditInitialValue] = useState('')
  const [discardedValue, setDiscardedValue] = useState('')
  const [pendingChanges, setPendingChanges] = useState<Map<string, string>>(
    new Map()
  )
  const activeAudioRef = useRef<HTMLAudioElement | null>(null)

  const tableHeaders = ['Name', "Hear speaker's voice", '']

  const handleEdit = useCallback(
    (speaker: string) => {
      const initialValue = pendingChanges.get(speaker) ?? speaker
      setEditingSpeaker(speaker)
      setEditInitialValue(initialValue)
      setView('edit')
    },
    [pendingChanges]
  )

  const handleUpdate = useCallback(
    (newName: string) => {
      if (!editingSpeaker) return
      setPendingChanges((prev) => {
        const next = new Map(prev)
        if (newName === editingSpeaker) {
          next.delete(editingSpeaker)
        } else {
          next.set(editingSpeaker, newName)
        }
        return next
      })
      setEditingSpeaker(undefined)
      setView('list')
    },
    [editingSpeaker]
  )

  const handleDone = async () => {
    for (const [original, updated] of pendingChanges.entries()) {
      await onSaveSpeaker(original, updated)
    }
    setPendingChanges(new Map())
    setView('list')
    setBanner({
      message: 'Speaker names updated',
      variant: 'success',
      title: 'Success',
    })
    onClose()
  }

  const handleClose = () => {
    setPendingChanges(new Map())
    setEditingSpeaker(undefined)
    setView('list')
    onClose()
  }

  return (
    <GovukModalDialogue
      open={open}
      onClose={view === 'confirm-discard' ? () => setView('edit') : handleClose}
      title={
        view === 'confirm-discard'
          ? ''
          : view === 'edit'
            ? `Edit ${editInitialValue}`
            : 'Edit speaker names'
      }
    >
      {view === 'list' ? (
        <>
          <p className="govuk-body">
            You can check the speaker&apos;s voice to confirm who it is
          </p>
          <table className="govuk-table">
            <thead className="govuk-table__head">
              <tr className="govuk-table__row">
                {tableHeaders.map((header) => (
                  <th key={header} scope="col" className="govuk-table__header">
                    {header}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="govuk-table__body">
              {Array.from(speakers.entries()).map(([speaker, entries]) => (
                <tr className="govuk-table__row" key={speaker}>
                  <th scope="row" className="govuk-table__header">
                    {pendingChanges.get(speaker) ?? speaker}
                  </th>
                  <td className="govuk-table__cell">
                    <div className="govuk-button-group">
                      {src &&
                        entries
                          .slice(0, 3)
                          .map((entry) => (
                            <PlayClipButton
                              key={entry.start_time}
                              src={src}
                              startTime={entry.start_time}
                              endTime={entry.end_time}
                              className="govuk-!-margin-right-3"
                              activeAudioRef={activeAudioRef}
                            />
                          ))}
                    </div>
                  </td>
                  <td className="govuk-table__cell">
                    <GovukButton
                      variant="link"
                      onClick={() => handleEdit(speaker)}
                    >
                      Edit
                    </GovukButton>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <GovukModalDialogueActions>
            <GovukButton
              type="button"
              onClick={handleDone}
              disabled={pendingChanges.size === 0}
            >
              Done
            </GovukButton>

            <GovukButton type="button" variant="link" onClick={handleClose}>
              Cancel
            </GovukButton>
          </GovukModalDialogueActions>
        </>
      ) : view === 'edit' ? (
        <InLineEditForm
          key={editInitialValue}
          name={editInitialValue}
          onUpdate={handleUpdate}
          onCancel={(currentValue) => {
            if (currentValue === editInitialValue) {
              setEditingSpeaker(undefined)
              setView('list')
            } else {
              setDiscardedValue(currentValue)
              setView('confirm-discard')
            }
          }}
        />
      ) : (
        <ModalConfirmationInterstitial
          title="Discard changes?"
          body="If you continue, your changes will not be saved."
          confirmLabel="Discard changes"
          onConfirm={() => {
            setEditInitialValue(
              pendingChanges.get(editingSpeaker ?? '') ?? editingSpeaker ?? ''
            )
            setView('edit')
          }}
          onCancel={() => {
            setEditInitialValue(discardedValue)
            setView('edit')
          }}
        />
      )}
    </GovukModalDialogue>
  )
}

const PlayClipButton = ({
  src,
  startTime,
  endTime,
  className,
  activeAudioRef,
}: {
  src: string
  startTime: number
  endTime: number
  className?: string
  activeAudioRef: RefObject<HTMLAudioElement | null>
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
      className={className ?? ''}
      onClick={() => {
        if (audioRef.current) {
          if (audioRef.current.paused) {
            if (
              activeAudioRef.current &&
              activeAudioRef.current !== audioRef.current
            ) {
              activeAudioRef.current.pause()
            }
            activeAudioRef.current = audioRef.current
            audioRef.current.play()
          } else {
            audioRef.current.pause()
          }
        }
      }}
    >
      {isPlaying ? <PauseButton /> : <PlayButton />}
    </button>
  )
}
