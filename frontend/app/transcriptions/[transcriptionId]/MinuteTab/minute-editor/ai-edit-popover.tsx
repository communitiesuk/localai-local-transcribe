'use client'

import {
  GovukButton,
  GovukList,
  GovukListItem,
  GovukModalDialogue,
  GovukModalDialogueActions,
  GovukNotificationBanner,
  GovukTextarea,
} from '@/components/govuk'
import { createMinuteVersionMinutesMinuteIdVersionsPostMutation } from '@/lib/client/@tanstack/react-query.gen'
import { useMutation } from '@tanstack/react-query'
import { useCallback, useState } from 'react'
import { useForm, useWatch } from 'react-hook-form'

type AIEditFormData = { instruction: string }

export const AiEditPopover = ({
  disabled,
  minuteId,
  minuteVersionId,
  onSuccess,
  onEditStart,
}: {
  disabled: boolean
  minuteId: string
  minuteVersionId: string
  onSuccess: () => void
  onEditStart?: () => void
}) => {
  const [open, setOpen] = useState(false)
  const form = useForm<AIEditFormData>()
  const instructionValue = useWatch({
    name: 'instruction',
    control: form.control,
  })
  const {
    mutate: saveEdit,
    isPending,
    isError,
    reset: resetSaveEdit,
  } = useMutation({
    ...createMinuteVersionMinutesMinuteIdVersionsPostMutation(),
  })
  const closeModal = () => {
    resetSaveEdit()
    setOpen(false)
  }
  const onSubmit = useCallback(
    ({ instruction }: AIEditFormData) => {
      if (instruction) {
        onEditStart?.()
        saveEdit(
          {
            path: { minute_id: minuteId },
            body: {
              content_source: 'ai_edit',
              ai_edit_instructions: { instruction, source_id: minuteVersionId },
            },
          },
          { onSuccess }
        )
      }
    },
    [minuteId, minuteVersionId, onSuccess, onEditStart, saveEdit]
  )
  return (
    <>
      <GovukButton
        type="button"
        variant="secondary"
        disabled={disabled}
        onClick={() => {
          resetSaveEdit()
          setOpen(true)
        }}
      >
        AI Edit
      </GovukButton>
      <GovukModalDialogue open={open} onClose={closeModal} title="AI edit">
        <form onSubmit={form.handleSubmit(onSubmit)}>
          {isError && (
            <GovukNotificationBanner
              variant="important"
              title="There is a problem"
              className="mb-[15px]"
            >
              <p className="govuk-notification-banner__heading">
                Something went wrong starting your AI edit. Please try again.
              </p>
            </GovukNotificationBanner>
          )}
          <p className="govuk-body">
            Local Transcribe can improve your document in various ways, for
            example:
          </p>
          <GovukList type="bullet">
            <GovukListItem>adding or removing information</GovukListItem>
            <GovukListItem>reordering content</GovukListItem>
            <GovukListItem>making the tone more or less formal</GovukListItem>
          </GovukList>
          <p className="govuk-hint">
            Describe what changes you&apos;d like to make to your document
          </p>
          <GovukTextarea
            id="ai-edit-instruction"
            {...form.register('instruction')}
          />
          <GovukModalDialogueActions className="govuk-!-margin-top-4">
            <GovukButton
              type="submit"
              disabled={!instructionValue?.trim() || isPending}
            >
              Apply Edit
            </GovukButton>
            <GovukButton type="button" variant="link" onClick={closeModal}>
              Cancel
            </GovukButton>
          </GovukModalDialogueActions>
        </form>
      </GovukModalDialogue>
    </>
  )
}
