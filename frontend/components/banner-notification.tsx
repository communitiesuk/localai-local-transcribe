'use client'

import { useEffect } from 'react'
import { useBannerStore } from '@/stores/use-banner-store'
import { GovukNotificationBanner } from '@/components/govuk/notification-banner'

export function BannerNotification() {
  const { banner, clearBanner } = useBannerStore()

  useEffect(() => {
    return () => {
      clearBanner()
    }
  }, [clearBanner])

  if (!banner) {
    return null
  }

  return (
    <>
      <GovukNotificationBanner title={banner.title} variant={banner.variant}>
        {banner.message}
        {banner.link && (
          <a href={banner.link.href} className="govuk-link">
            {banner.link.text}
          </a>
        )}
      </GovukNotificationBanner>
    </>
  )
}
