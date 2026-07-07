import { GovukBackLink } from '@/components/govuk'
import { ReactNode } from 'react'

export default async function TemplatesLayout({
  children,
}: {
  children: ReactNode
}) {
  return (
    <div className="p-6 pt-1">
      <GovukBackLink />
      {children}
    </div>
  )
}
