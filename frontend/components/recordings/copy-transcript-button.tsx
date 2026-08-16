'use client'

import { GovukButton } from '@/components/govuk'
import { TranscriptReviewModal } from '@/components/recordings/transcript-review-modal'
import posthog from 'posthog-js'
import { useBannerStore } from '@/stores/use-banner-store'
import { useState } from 'react'

interface CopyTranscriptButtonProps {
  textToCopy: string
  onSuccess: () => void
}

export function CopyTranscriptButton({
  textToCopy,
  onSuccess,
}: CopyTranscriptButtonProps) {
  const [modalOpen, setModalOpen] = useState(false)
  const { setBanner } = useBannerStore()

  const stripHtmlTags = (html: string) => {
    const tmp = document.createElement('DIV')
    tmp.innerHTML = html
    return tmp.textContent || tmp.innerText || ''
  }

  const handleConfirm = async () => {
    try {
      await navigator.clipboard.write([
        new ClipboardItem({
          'text/html': new Blob([textToCopy], { type: 'text/html' }),
          'text/plain': new Blob([stripHtmlTags(textToCopy)], {
            type: 'text/plain',
          }),
        }),
      ])
    } catch {
      try {
        await navigator.clipboard.writeText(stripHtmlTags(textToCopy))
      } catch {
        setModalOpen(false)
        setBanner({
          variant: 'important',
          title: 'Error',
          message: 'Error copying transcript.',
        })
        return
      }
    }

    posthog.capture('transcript_content_copied', {
      contentLength: textToCopy.length,
    })

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
      >
        Copy transcript
      </GovukButton>

      <TranscriptReviewModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onConfirm={handleConfirm}
        titleId="copy-transcript-modal-title"
      />
    </>
  )
}
