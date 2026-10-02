'use client'

import { useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'

import { useUploadRecordingStore } from '@/stores/use-upload-recording-store'
import { useOnlineStatus } from '@/hooks/use-online-status'
import { useLockNavigation } from '@/hooks/use-lock-navigation-context'
import { ProcessingSpinner } from '@/components/processing-spinner'
import { GovukButton, GovukHeading } from '@/components/govuk'

const LOCK_NAVIGATION_MESSAGE =
  'You have a recording that has not been uploaded. Are you sure you want to leave this page? Your recording will be discarded if you do not upload it.'

export function UploadStatus() {
  const router = useRouter()
  const hasRedirectedToMetadataRef = useRef(false)
  const isOnline = useOnlineStatus()

  const {
    status,
    transcriptionId,
    uploadingFrom,
    awaitingManualRetry,
    reset,
    retryUpload,
  } = useUploadRecordingStore()

  useLockNavigation(
    status === 'pending' || status === 'error' ? LOCK_NAVIGATION_MESSAGE : false
  )

  useEffect(() => {
    if (status === 'success' && transcriptionId) {
      hasRedirectedToMetadataRef.current = true
      reset()
      router.push(`/new/metadata/${transcriptionId}`)
    }
  }, [status, transcriptionId, reset, router])

  const needsRetry =
    status === 'error' || (status === 'pending' && awaitingManualRetry)

  if (needsRetry) {
    const heading =
      status === 'error'
        ? 'We could not upload your recording'
        : isOnline
          ? 'Ready to retry'
          : 'Waiting to reconnect'

    const message =
      status === 'error'
        ? "Something went wrong while uploading your recording. It's still held on this device, so you can try again but it will be lost if you leave this page without uploading it."
        : isOnline
          ? "You're back online. Your recording is safely held on this device. Select retry to upload it."
          : "You're currently offline. Your recording is safely held on this device. Once your connection returns, select retry to upload it. Don't close this tab or navigate away, your recording will be lost if you leave now."

    return (
      <div className="space-y-4">
        <GovukHeading>{heading}</GovukHeading>
        <p
          className={status === 'error' ? 'govuk-error-message' : 'govuk-body'}
          role={status === 'error' ? 'alert' : undefined}
        >
          {status === 'error' && (
            <span className="govuk-visually-hidden">Error: </span>
          )}
          {message}
        </p>
        <GovukButton
          type="button"
          onClick={() => retryUpload()}
          disabled={!isOnline}
        >
          Retry
        </GovukButton>
      </div>
    )
  }

  return (
    <ProcessingSpinner
      label={uploadingFrom === 'upload' ? 'Uploading' : 'Processing'}
      message={`${uploadingFrom === 'upload' ? 'Uploading File' : 'Processing recording'}…`}
    />
  )
}
