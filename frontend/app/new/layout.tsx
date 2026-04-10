import { ReactNode } from 'react'

export default function NewLayout({ children }: { children: ReactNode }) {
  return <div className="mx-auto max-w-3xl pt-1">{children}</div>
}
