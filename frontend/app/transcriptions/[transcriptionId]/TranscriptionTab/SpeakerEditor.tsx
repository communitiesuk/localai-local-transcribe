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
  disabled = false,
}: {
  src?: string
  onSaveSpeaker: (originalSpeaker: string, newSpeaker: string) => Promise<void>
  disabled?: boolean
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
        disabled={disabled}
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
  const [pendingChanges, setPendingChanges] = useState<Map<string, string>>(
    new Map()
  )
  const [inFlightRequest, setInFlightRequest] = useState(false)

  const activeAudioRef = useRef<HTMLAudioElement | null>(null)

  const tableHeaders: React.ReactNode[] = [
    'Name',
    "Hear speaker's voice",
    <span key="actions" className="govuk-visually-hidden">
      Actions
    </span>,
  ]

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
    setInFlightRequest(true)
    for (const [original, updated] of pendingChanges.entries()) {
      try {
        await onSaveSpeaker(original, updated)
      } catch (error) {
        console.error(
          `Error saving speaker name change from ${original} to ${updated}:`,
          error
        )
        setBanner({
          message: `One or more speaker names could not be updated, please try again.`,
          variant: 'important',
          title: 'Error',
        })
        setInFlightRequest(false)
        return
      }
    }
    setInFlightRequest(false)
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
      onClose={
        view === 'confirm-discard'
          ? () => setView('list')
          : view === 'edit'
            ? () => {
                setEditingSpeaker(undefined)
                setView('list')
              }
            : pendingChanges.size > 0
              ? () => setView('confirm-discard')
              : handleClose
      }
      title={
        view === 'edit'
          ? `Edit ${editInitialValue}`
          : view === 'confirm-discard'
            ? ''
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
                {tableHeaders.map((header, index) => (
                  <th key={index} scope="col" className="govuk-table__header">
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
              disabled={pendingChanges.size === 0 || inFlightRequest}
            >
              Done
            </GovukButton>

            <GovukButton
              type="button"
              variant="link"
              onClick={
                pendingChanges.size > 0
                  ? () => setView('confirm-discard')
                  : handleClose
              }
            >
              Cancel
            </GovukButton>
          </GovukModalDialogueActions>
        </>
      ) : view === 'edit' ? (
        <InLineEditForm
          key={editInitialValue}
          name={editInitialValue}
          onUpdate={handleUpdate}
          onCancel={() => {
            setEditingSpeaker(undefined)
            setView('list')
          }}
        />
      ) : (
        <ModalConfirmationInterstitial
          title="Discard changes?"
          body={
            <div className="govuk-warning-text">
              <span className="govuk-warning-text__icon" aria-hidden="true">
                !
              </span>
              <strong className="govuk-warning-text__text">
                <span className="govuk-visually-hidden">Warning</span>
                If you continue, your changes will not be saved.
              </strong>
            </div>
          }
          confirmLabel="Discard changes"
          onConfirm={() => {
            setPendingChanges(new Map())
            setView('list')
            handleClose()
          }}
          onCancel={() => setView('list')}
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
