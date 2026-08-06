'use client'

import { GovukBackLink } from '@/components/govuk'
import { usePathname } from 'next/navigation'

// The confirmation interstitials (save/duplicate/delete/cancel) are reached
// from the edit page and dismissed via their own Cancel button rather than a
// back link.
const INTERSTITIAL_ROUTE = /\/templates\/[^/]+\/(save|duplicate|delete|cancel)$/

export function TemplatesBackLink() {
  const pathname = usePathname()

  if (pathname && INTERSTITIAL_ROUTE.test(pathname)) {
    return null
  }

  return <GovukBackLink />
}
