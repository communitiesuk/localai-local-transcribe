'use client'

import { initAnalytics } from '@/lib/analytics'
import { useEffect } from 'react'

export function PlausibleInit() {
  useEffect(() => {
    initAnalytics()
  }, [])

  return null
}
