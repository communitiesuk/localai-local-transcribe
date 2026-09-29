'use client'

import { usePathname } from 'next/navigation'
import { useEffect, useRef } from 'react'

import { useUploadRecordingStore } from '@/stores/use-upload-recording-store'

export function RouteWatcher() {
  const pathname = usePathname()
  const previousPathnameRef = useRef(pathname)

  useEffect(() => {
    if (previousPathnameRef.current === pathname) {
      return
    }

    previousPathnameRef.current = pathname
    useUploadRecordingStore.getState().cancelRequest()
  }, [pathname])

  return null
}
