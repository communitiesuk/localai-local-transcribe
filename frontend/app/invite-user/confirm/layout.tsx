import React, { Suspense, ReactNode } from 'react'
import { HistoryBackButton } from '@/components/ui/history-back-button'

export default function InviteUserConfirmLayout({
  children,
}: {
  children: ReactNode
}) {
  return (
    <div className="p-6 pt-1">
      <HistoryBackButton />
      <Suspense fallback={<div>Loading…</div>}>{children}</Suspense>
    </div>
  )
}
