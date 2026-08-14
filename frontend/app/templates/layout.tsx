import { TemplatesBackLink } from '@/app/templates/components/templates-back-link'
import { ReactNode } from 'react'

export default async function TemplatesLayout({
  children,
}: {
  children: ReactNode
}) {
  return (
    <div className="p-6 pt-1">
      <TemplatesBackLink />
      {children}
    </div>
  )
}
