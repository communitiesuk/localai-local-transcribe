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
