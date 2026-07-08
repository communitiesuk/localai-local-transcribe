import { ReactNode } from 'react'
import { GovukBackLink } from '@/components/govuk'

export default function AdminAddUserLayout({
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
