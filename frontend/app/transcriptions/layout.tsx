import { ReactNode } from 'react'
import { GovukBackLink } from '@/components/govuk'

export default function TranscriptionsLayout({
  children,
}: {
  children: ReactNode
}) {
  return (
    <div className="p-6">
      <GovukBackLink />
      {children}
    </div>
  )
}
