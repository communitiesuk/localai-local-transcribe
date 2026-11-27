'use client'

import { GovukBackLink } from '@/components/govuk'
import { usePathname } from 'next/navigation'

// The delete confirmation interstitial is dismissed via its own Cancel link
// rather than a back link.
const INTERSTITIAL_ROUTE = /\/transcriptions\/[^/]+\/delete$/

export function TranscriptionBackLink() {
  const pathname = usePathname()

  if (pathname && INTERSTITIAL_ROUTE.test(pathname)) {
    return null
  }

  return <GovukBackLink />
}
