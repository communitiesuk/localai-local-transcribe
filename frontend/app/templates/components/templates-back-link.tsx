'use client'

import { GovukBackLink } from '@/components/govuk'
import { usePathname } from 'next/navigation'

// The confirmation interstitials (the create confirm page, and the edit flow's
// save/duplicate/delete/cancel pages) are dismissed via their own Cancel button
// rather than a back link.
const INTERSTITIAL_ROUTE =
  /\/templates\/[^/]+\/(save|duplicate|delete|cancel|confirm)$/

export function TemplatesBackLink() {
  const pathname = usePathname()

  if (pathname && INTERSTITIAL_ROUTE.test(pathname)) {
    return null
  }

  return <GovukBackLink />
}
