'use client'

import * as Sentry from '@sentry/nextjs'
import { useEffect } from 'react'

export function GovukInit() {
  useEffect(() => {
    let cancelled = false
    import('govuk-frontend')
      .then(({ initAll }) => {
        if (!cancelled) initAll()
      })
      .catch((err) => {
        console.error('govuk-frontend init failed', err)
        Sentry.captureException(err)
      })
    return () => {
      cancelled = true
    }
  }, [])

  return null
}
