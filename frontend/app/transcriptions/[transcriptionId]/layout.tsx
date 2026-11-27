import { ReactNode } from 'react'
import { TranscriptionBackLink } from '@/app/transcriptions/[transcriptionId]/components/transcription-back-link'

export default function TranscriptionLayout({
  children,
}: {
  children: ReactNode
}) {
  return (
    <div>
      <TranscriptionBackLink />
      {children}
    </div>
  )
}
