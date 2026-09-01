'use client'

import { useBannerStore } from '@/stores/use-banner-store'
import { useUploadRecordingStore } from '@/stores/use-upload-recording-store'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'

export default function TranscriptionLoadingPage() {
  const router = useRouter()
  const setBanner = useBannerStore((store) => store.setBanner)

  const { status, transcriptionId, uploadingFrom, error, reset } =
    useUploadRecordingStore()

  useEffect(() => {
    if (status === 'success' && transcriptionId) {
      reset()

      if (uploadingFrom === 'in-person-recording') {
        router.push(`/transcriptions/${transcriptionId}?details=open`)
        return
      }

      setBanner({
        variant: 'success',
        title: 'Success',
        message: 'Recording saved - ',
        link: {
          text: 'click to view',
          href: `/transcriptions/${transcriptionId}`,
        },
      })

      router.push('/')
    }

    if (status === 'idle') {
      router.replace('/')
    }
  }, [status, transcriptionId, uploadingFrom, setBanner, reset, router])

  if (status === 'error') {
    throw new Error(error || 'Upload failed')
  }

  return (
    <div className="flex flex-col items-center">
      {/* spinner */}
      <div
        aria-label={uploadingFrom === 'upload' ? 'Uploading' : 'Processing'}
        aria-live="polite"
        role="status"
        className="mb-5 h-28 w-28 animate-spin rounded-full border-[12px] border-gray-400 border-t-sky-700"
      />
      <p className="govuk-body">
        {uploadingFrom === 'upload' ? 'Uploading File' : 'Processing recording'}
        &hellip;
      </p>
    </div>
  )
}
