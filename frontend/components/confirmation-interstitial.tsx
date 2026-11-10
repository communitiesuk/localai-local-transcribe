'use client'

import { GovukButton, GovukButtonGroup } from '@/components/govuk'
import { ProcessingSpinner } from '@/components/processing-spinner'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { ReactNode } from 'react'

type ActionVariant = 'primary' | 'secondary' | 'warning' | 'inverse'

type ConfirmationInterstitialProps = {
  title: string
  children: ReactNode
  actionLabel: string
  actionVariant?: ActionVariant
  onAction: () => void
  actionPending?: boolean
  pendingLabel?: string
  // Cancelling navigates back through history rather than by pushing this URL,
  // but an href is still required for accessibility / graceful degradation.
  cancelHref: string
  cancelLabel?: string
}

export function ConfirmationInterstitial({
  title,
  children,
  actionLabel,
  actionVariant = 'primary',
  onAction,
  actionPending,
  pendingLabel,
  cancelHref,
  cancelLabel = 'Cancel',
}: ConfirmationInterstitialProps) {
  const router = useRouter()

  // Pop the interstitial off the history stack and don't push the cancelHref
  // so it never becomes a back-navigation target from the page we return to.
  const handleCancel = (event: React.MouseEvent<HTMLAnchorElement>) => {
    event.preventDefault()
    router.back()
  }

  if (actionPending && pendingLabel) {
    return (
      <ProcessingSpinner label={pendingLabel} message={`${pendingLabel}…`} />
    )
  }

  return (
    <div>
      <h1 className="govuk-heading-l break-words">{title}</h1>
      <div className="govuk-grid-row">
        <div className="govuk-grid-column-three-quarters break-words">
          {children}
        </div>
      </div>
      <GovukButtonGroup className="govuk-!-margin-top-2">
        <GovukButton
          type="button"
          variant={actionVariant}
          onClick={onAction}
          disabled={actionPending}
        >
          {actionLabel}
        </GovukButton>
        <Link href={cancelHref} className="govuk-link" onClick={handleCancel}>
          {cancelLabel}
        </Link>
      </GovukButtonGroup>
    </div>
  )
}
