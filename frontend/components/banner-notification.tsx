'use client'

import { useBannerStore } from '@/stores/use-banner-store'

export function BannerNotification() {
  const message = useBannerStore((store) => store.message)
  const clearBanner = useBannerStore((store) => store.clearBanner)

  if (!message) {
    return null
  }

  return (
    <div>
      <p>Toast goes here</p>
      <p>{message}</p>
      <button onClick={clearBanner}>Dismiss</button>
    </div>
  )
}
