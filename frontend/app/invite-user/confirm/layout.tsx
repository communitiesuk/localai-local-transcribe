import React, { Suspense, ReactNode } from 'react'

export default function InviteUserConfirmLayout({
  children,
}: {
  children: ReactNode
}) {
  return (
    <div className="p-6 pt-1">
      <Suspense fallback={<div>Loading…</div>}>{children}</Suspense>
    </div>
  )
}
