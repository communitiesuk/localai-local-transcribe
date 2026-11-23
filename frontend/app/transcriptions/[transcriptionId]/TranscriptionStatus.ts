import { Banner, useBannerStore } from '@/stores/use-banner-store'
import { useRouter } from 'next/navigation'

type Router = ReturnType<typeof useRouter>
type SetBanner = ReturnType<typeof useBannerStore.getState>['setBanner']

export const isTranscriptionProcessing = (status: string | null | undefined) =>
  !!status && ['awaiting_start', 'in_progress'].includes(status)

const notifyAndReturnHome = (
  router: Router,
  setBanner: SetBanner,
  banner: Pick<Banner, 'variant' | 'title' | 'message'>,
  href: string
) => {
  setBanner({ ...banner, link: { text: 'click to view', href } })
  router.push('/')
}

export const notifyRecordingSaved = (
  router: Router,
  setBanner: SetBanner,
  transcriptionId: string
) =>
  notifyAndReturnHome(
    router,
    setBanner,
    { variant: 'success', title: 'Success', message: 'Recording saved - ' },
    `/transcriptions/${transcriptionId}?details=open`
  )

export const notifyRecordingFailed = (
  router: Router,
  setBanner: SetBanner,
  transcriptionId: string
) =>
  notifyAndReturnHome(
    router,
    setBanner,
    {
      variant: 'important',
      title: 'Error',
      message: 'Transcription failed - ',
    },
    `/transcriptions/${transcriptionId}`
  )

export const notifyNoSpeechDetected = (
  router: Router,
  setBanner: SetBanner,
  transcriptionId: string
) =>
  notifyAndReturnHome(
    router,
    setBanner,
    {
      variant: 'important',
      title: 'Important',
      message: 'No speech was detected in your recording - ',
    },
    `/transcriptions/${transcriptionId}`
  )
