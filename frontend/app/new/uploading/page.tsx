'use client'

import { useUploadRecordingStore } from '@/stores/use-upload-recording-store'
import { ProcessingSpinner } from '@/components/processing-spinner'
import { useRouter } from 'next/navigation'
import { useEffect, useRef } from 'react'

export default function TranscriptionLoadingPage() {
  const router = useRouter()
  const hasRedirectedToMetadataRef = useRef(false)

  const { status, transcriptionId, uploadingFrom, error, reset } =
    useUploadRecordingStore()

  useEffect(() => {
    if (status === 'success' && transcriptionId) {
      hasRedirectedToMetadataRef.current = true
      reset()
      router.push(`/new/metadata/${transcriptionId}`)
      return
    }

    if (status === 'idle' && !hasRedirectedToMetadataRef.current) {
      router.replace('/')
    }
  }, [status, transcriptionId, uploadingFrom, reset, router])

  if (status === 'error') {
    throw new Error(error || 'Upload failed')
  }

  return (
    <ProcessingSpinner
      label={uploadingFrom === 'upload' ? 'Uploading' : 'Processing'}
      message={`${uploadingFrom === 'upload' ? 'Uploading File' : 'Processing recording'}…`}
    />
  )
}
