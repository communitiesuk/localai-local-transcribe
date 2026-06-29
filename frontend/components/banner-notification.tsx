'use client'

import { useBannerStore } from '@/stores/use-banner-store'
import { GovukNotificationBanner } from '@/components/govuk/banner'

export function BannerNotification() {
  const { banner } = useBannerStore()

  if (!banner) {
    return null
  }

  return (
    <>
      <GovukNotificationBanner title={banner.title} variant={banner.variant}>
        {banner.message}
      </GovukNotificationBanner>
    </>
  )
}
