'use client'

import { useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'

import { useUploadRecordingStore } from '@/stores/use-upload-recording-store'
import { UploadStatus } from '@/components/audio/upload-status'
export default function TranscriptionLoadingPage() {
  const router = useRouter()
  const hasLeftIdleRef = useRef(false)
  const status = useUploadRecordingStore((store) => store.status)

  useEffect(() => {
    if (status !== 'idle') {
      hasLeftIdleRef.current = true
      return
    }

    if (!hasLeftIdleRef.current) {
      router.replace('/')
    }
  }, [status, router])

  return <UploadStatus />
}
