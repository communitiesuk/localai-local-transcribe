'use client'
// Based on the MoJ's design system
//https://design-patterns.service.justice.gov.uk/components/modal-dialog/#code-tab

import { useEffect, useRef } from 'react'
import { createPortal } from 'react-dom'
import { cn } from '@/lib/utils'

type Props = {
  open: boolean
  onClose: () => void
  titleId?: string
  descriptionId?: string
  title: string
  className?: string
  children?: React.ReactNode
}

export function GovukModalDialogue({
  open,
  onClose,
  titleId = 'govuk-modal-dialogue-title',
  descriptionId = 'govuk-modal-dialogue-description',
  title,
  className,
  children,
}: Props) {
  const dialogRef = useRef<HTMLDialogElement>(null)

  useEffect(() => {
    if (open) {
      dialogRef.current?.focus()
    }
  }, [open])

  // Toggle inert on the page content container so background content is
  // inaccessible to keyboard and assistive technology while the modal is open.
  // This replicates what GOV.UK Frontend's JS does via data-inert-container.
  useEffect(() => {
    const container = document.querySelector<HTMLElement>(
      '.govuk-modal-dialogue-inert-container'
    )
    if (!container) return
    if (open) {
      container.setAttribute('inert', '')
    } else {
      container.removeAttribute('inert')
    }
    return () => {
      container.removeAttribute('inert')
    }
  }, [open])

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape' && open) onClose()
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [open, onClose])

  if (!open || typeof document === 'undefined') return null

  return createPortal(
    <div className="govuk-modal-dialogue govuk-modal-dialogue--open">
      <div
        className="govuk-modal-dialogue__wrapper"
        onClick={(e) => {
          if (e.target === e.currentTarget) onClose()
        }}
      >
        <dialog
          ref={dialogRef}
          className={cn('govuk-modal-dialogue__box', className)}
          aria-labelledby={titleId}
          aria-describedby={descriptionId}
          aria-modal="true"
          tabIndex={-1}
          open
        >
          <div className="govuk-modal-dialogue__header">
            <button
              type="button"
              className="govuk-button govuk-modal-dialogue__close"
              aria-label="Close"
              onClick={onClose}
            >
              ✕
            </button>
          </div>
          <div className="govuk-modal-dialogue__content">
            <h2
              className="govuk-modal-dialogue__heading govuk-heading-l"
              id={titleId}
            >
              {title}
            </h2>
            <div
              className="govuk-modal-dialogue__description govuk-body"
              id={descriptionId}
            >
              {children}
            </div>
          </div>
        </dialog>
      </div>
      <div className="govuk-modal-dialogue__backdrop" />
    </div>,
    document.body
  )
}

type ActionsProps = {
  className?: string
  children: React.ReactNode
} & Omit<React.HTMLAttributes<HTMLDivElement>, 'className' | 'children'>

export function GovukModalDialogueActions({
  className,
  children,
  ...rest
}: ActionsProps) {
  return (
    <div {...rest} className={cn('govuk-button-group', className)}>
      {children}
    </div>
  )
}
