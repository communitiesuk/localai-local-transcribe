'use client'

import { usePathname } from 'next/navigation'
import { useEffect, useRef } from 'react'

import { useTemplateDraftStore } from '@/stores/use-template-draft-store'
import { useUploadRecordingStore } from '@/stores/use-upload-recording-store'

export function RouteWatcher() {
  const pathname = usePathname()
  const previousPathnameRef = useRef(pathname)

  useEffect(() => {
    if (previousPathnameRef.current === pathname) {
      return
    }

    previousPathnameRef.current = pathname
    useUploadRecordingStore.getState().handleRouteChange()
    useTemplateDraftStore.getState().handleRouteChange(pathname)
  }, [pathname])

  return null
}
