'use client'

import { useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'

import { useUploadRecordingStore } from '@/stores/use-upload-recording-store'
import { useOnlineStatus } from '@/hooks/use-online-status'
import { useTabCloseWarning } from '@/hooks/use-tab-close-warning'
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
    error,
    awaitingManualRetry,
    reset,
    retryUpload,
  } = useUploadRecordingStore()

  useTabCloseWarning(
    status === 'pending' || status === 'error' ? LOCK_NAVIGATION_MESSAGE : false
  )

  useEffect(() => {
    if (status === 'success' && transcriptionId) {
      hasRedirectedToMetadataRef.current = true
      reset()
      router.push(`/new/metadata/${transcriptionId}`)
    }
  }, [status, transcriptionId, reset, router])

  if (status === 'error') {
    return (
      <div className="space-y-4">
        <GovukHeading>We could not upload your recording</GovukHeading>
        <p className="govuk-error-message" role="alert">
          <span className="govuk-visually-hidden">Error:</span> Something went
          wrong while uploading your recording{error ? ` (${error})` : ''}.
          It&apos;s still held on this device, so you can try again — but it
          will be lost if you leave this page without uploading it.
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

  if (status === 'pending' && awaitingManualRetry) {
    return (
      <div className="space-y-4">
        <GovukHeading>
          {isOnline ? 'Ready to retry' : 'Waiting to reconnect'}
        </GovukHeading>
        <p className="govuk-body">
          {isOnline
            ? "You're back online. Your recording is safely held on this device. Select retry to upload it."
            : "You're currently offline. Your recording is safely held on this device. Once your connection returns, select retry to upload it. Don't close this tab or navigate away, your recording will be lost if you leave now."}
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
