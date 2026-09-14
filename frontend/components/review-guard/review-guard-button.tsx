'use client'

import { useState } from 'react'
import { useBannerStore } from '@/stores/use-banner-store'
import { GovukButton } from '@/components/govuk'
import { ReviewGuardModal } from '@/components/review-guard/review-guard-modal'

interface ReviewGuardButtonProps {
  onConfirm: () => boolean | Promise<boolean>
  onSuccess: () => void | Promise<void>
  disabled?: boolean
  className?: string
  // following props used only for wording/modal id
  action: 'copy' | 'download'
  subject: 'transcript' | 'document'
}

export function ReviewGuardButton({
  onConfirm,
  onSuccess,
  disabled,
  className,
  action,
  subject,
}: ReviewGuardButtonProps) {
  const [modalOpen, setModalOpen] = useState(false)
  const { setBanner } = useBannerStore()

  const handleConfirm = async () => {
    setModalOpen(false)
    try {
      const success = await onConfirm()
      if (success) {
        await onSuccess()
      }
    } catch {
      setBanner({
        variant: 'important',
        title: 'Error',
        message: `Error ${action === 'copy' ? 'copying' : 'downloading'} ${subject}.`,
      })
    }
  }

  return (
    <>
      <GovukButton
        type="button"
        variant="secondary"
        onClick={() => setModalOpen(true)}
        disabled={disabled}
        className={className}
      >
        {action === 'copy' ? 'Copy' : 'Download'} {subject}
      </GovukButton>

      <ReviewGuardModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onConfirm={handleConfirm}
        action={action}
        subject={subject}
      />
    </>
  )
}
