'use client'

import { useEffect, useRef } from 'react'
import { useBannerStore } from '@/stores/use-banner-store'
import { GovukNotificationBanner } from '@/components/govuk/notification-banner'

export function BannerNotification() {
  const { banner, clearBanner } = useBannerStore()
  const bannerRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    return () => {
      clearBanner()
    }
  }, [clearBanner])

  useEffect(() => {
    if (banner && bannerRef.current) {
      bannerRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }, [banner])

  if (!banner) {
    return null
  }

  return (
    <div ref={bannerRef}>
      <GovukNotificationBanner title={banner.title} variant={banner.variant}>
        {banner.message}
      </GovukNotificationBanner>
    </div>
  )
}
