'use client'

import { GovukButton } from '@/components/govuk'
import { TranscriptReviewModal } from '@/components/recordings/transcript-review-modal'
import { DialogueEntry } from '@/lib/client'
import { downloadTranscriptDoc } from '@/lib/download-word-doc'
import { useState } from 'react'

interface DownloadTranscriptButtonProps {
  getEntries: () => DialogueEntry[]
  onSuccess: () => void
}

export function DownloadTranscriptButton({
  getEntries,
  onSuccess,
}: DownloadTranscriptButtonProps) {
  const [modalOpen, setModalOpen] = useState(false)

  const handleConfirm = async () => {
    setModalOpen(false)
    await downloadTranscriptDoc(getEntries())
    onSuccess()
  }

  return (
    <>
      <GovukButton
        type="button"
        variant="secondary"
        onClick={() => setModalOpen(true)}
        className="govuk-!-margin-bottom-0"
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
