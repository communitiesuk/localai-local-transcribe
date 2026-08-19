'use client'

import { GovukButton } from '@/components/govuk'
import { TranscriptReviewModal } from '@/components/recordings/transcript-review-modal'
import { DialogueEntry } from '@/lib/client'
import { downloadTranscriptDoc } from '@/lib/download-word-doc'
import { useBannerStore } from '@/stores/use-banner-store'
import { useState } from 'react'
import { formatDate } from '@/lib/utils'

interface DownloadTranscriptButtonProps {
  getEntries: () => DialogueEntry[]
  onSuccess: () => void
  createdDatetime?: string
  disabled?: boolean
}

export function DownloadTranscriptButton({
  getEntries,
  onSuccess,
  createdDatetime,
  disabled,
}: DownloadTranscriptButtonProps) {
  const [modalOpen, setModalOpen] = useState(false)
  const { setBanner } = useBannerStore()

  const handleConfirm = async () => {
    const formatted = createdDatetime ? formatDate(createdDatetime) : null
    const timeStamp = formatted ? `-${formatted}` : ''
    const fileName = `transcript${timeStamp}.docx`

    try {
      await downloadTranscriptDoc(getEntries(), fileName)
    } catch {
      setModalOpen(false)
      setBanner({
        variant: 'important',
        title: 'Error',
        message: 'Error downloading transcript.',
      })
      return
    }

    setModalOpen(false)
    onSuccess()
  }

  return (
    <>
      <GovukButton
        type="button"
        variant="secondary"
        onClick={() => setModalOpen(true)}
        className="govuk-!-margin-bottom-0"
        disabled={disabled}
      >
        Download transcript
      </GovukButton>

      <TranscriptReviewModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onConfirm={handleConfirm}
        titleId="download-transcript-modal-title"
      />
    </>
  )
}
