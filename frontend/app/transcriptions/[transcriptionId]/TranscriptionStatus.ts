import { useBannerStore } from '@/stores/use-banner-store'
import { useRouter } from 'next/navigation'

export const isTranscriptionProcessing = (status: string | null | undefined) =>
  !!status && ['awaiting_start', 'in_progress'].includes(status)

export const notifyRecordingSaved = (
  router: ReturnType<typeof useRouter>,
  setBanner: ReturnType<typeof useBannerStore.getState>['setBanner'],
  transcriptionId: string
) => {
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

export const notifyRecordingFailed = (
  router: ReturnType<typeof useRouter>,
  setBanner: ReturnType<typeof useBannerStore.getState>['setBanner'],
  transcriptionId: string
) => {
  setBanner({
    variant: 'important',
    title: 'Error',
    message: 'Transcription failed - ',
    link: {
      text: 'click to view',
      href: `/transcriptions/${transcriptionId}`,
    },
  })
  router.push('/')
}
