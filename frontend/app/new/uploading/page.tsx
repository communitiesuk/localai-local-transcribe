'use client'

import { useBannerStore } from '@/stores/use-banner-store'
import { useUploadRecordingStore } from '@/stores/use-upload-recording-store'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'

export default function TranscriptionLoadingPage() {
  const router = useRouter()
  const setBanner = useBannerStore((store) => store.setBanner)

  const status = useUploadRecordingStore((store) => store.status)
  const transcriptionId = useUploadRecordingStore(
    (store) => store.transcriptionId
  )
  const error = useUploadRecordingStore((store) => store.error)
  const reset = useUploadRecordingStore((store) => store.reset)

  useEffect(() => {
    if (status === 'success' && transcriptionId) {
      setBanner({
        variant: 'success',
        title: 'Success',
        message: 'Recording saved - ',
        link: {
          text: 'click to view',
          href: `/transcriptions/${transcriptionId}`,
        },
      })

      reset()
      router.push('/')
    }

    if (status === 'error') {
      router.replace('/generic-error')
    }
  }, [status, transcriptionId, error, setBanner, reset, router])

  return (
    <div className="flex flex-col items-center">
      {/* spinner */}
      <div
        aria-label="Uploading"
        className="mb-5 h-28 w-28 animate-spin rounded-full border-[12px] border-gray-400 border-t-sky-700"
      />
      <p className="govuk-body">Uploading File...</p>
    </div>
  )
}
