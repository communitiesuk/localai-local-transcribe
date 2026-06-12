import { ReactNode } from 'react'
import { HistoryBackButton } from '@/components/ui/history-back-button'

export default function AdminAddUserLayout({
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
