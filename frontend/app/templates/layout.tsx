import { HistoryBackButton } from '@/components/ui/history-back-button'
import { ReactNode } from 'react'

export default async function TemplatesLayout({
  children,
}: {
  children: ReactNode
}) {
  return (
    <div className="p-6 pt-1">
      <HistoryBackButton />
      {children}
    </div>
  )
}
