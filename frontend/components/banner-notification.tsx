'use client'

import { useEffect, useRef } from 'react'
import { usePathname } from 'next/navigation'
import { type Banner, useBannerStore } from '@/stores/use-banner-store'
import { GovukNotificationBanner } from '@/components/govuk/notification-banner'

let displayedBanner: Banner | null = null
let displayedPath: string | null = null

const resetDisplayedBanner = () => {
  displayedBanner = null
  displayedPath = null
}

export function useClearDisplayedBannerOnRouteChange() {
  const banner = useBannerStore((store) => store.banner)
  const clearBanner = useBannerStore((store) => store.clearBanner)
  const pathname = usePathname()

  useEffect(() => {
    if (banner && displayedBanner === banner && displayedPath !== pathname) {
      clearBanner()
      resetDisplayedBanner()
    }
  }, [banner, clearBanner, pathname])
}

export function BannerNotification() {
  const banner = useBannerStore((store) => store.banner)
  const clearBanner = useBannerStore((store) => store.clearBanner)
  const pathname = usePathname()
  const bannerRef = useRef<HTMLDivElement | null>(null)
  const isStaleBanner =
    banner && displayedBanner === banner && displayedPath !== pathname

  useEffect(() => {
    if (!banner) {
      resetDisplayedBanner()
      return
    }

    if (displayedBanner !== banner) {
      displayedBanner = banner
      displayedPath = pathname
      return
    }

    if (isStaleBanner) {
      clearBanner()
      resetDisplayedBanner()
    }
  }, [banner, clearBanner, isStaleBanner, pathname])

  useEffect(() => {
    if (banner && !isStaleBanner && bannerRef.current) {
      bannerRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }, [banner, isStaleBanner])

  if (!banner || isStaleBanner) {
    return null
  }

  return (
    <div ref={bannerRef}>
      <GovukNotificationBanner title={banner.title} variant={banner.variant}>
        {banner.message}
        {banner.link && (
          <a href={banner.link.href} className="govuk-link">
            {banner.link.text}
          </a>
        )}
      </GovukNotificationBanner>
    </div>
  )
}
