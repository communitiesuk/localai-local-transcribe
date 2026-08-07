'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'

import { GovukBody, GovukLink } from '@/components/govuk'

export function RecordingLoading({
  nextPath,
  cancelPath,
}: {
  nextPath: string
  cancelPath: string
}) {
  const router = useRouter()
  const [countdown, setCountdown] = useState(3)

  useEffect(() => {
    if (countdown === 0) {
      router.replace(nextPath)
      return
    }

    const timeoutId = window.setTimeout(() => {
      setCountdown((currentCountdown) => currentCountdown - 1)
    }, 1000)

    return () => window.clearTimeout(timeoutId)
  }, [countdown, nextPath, router])

  return (
    <div className="govuk-!-text-align-centre">
      <GovukBody size="l">Recording starts in...</GovukBody>
      <p className="mb-7 text-5xl font-bold">{countdown}</p>
      <GovukLink href={cancelPath}>cancel</GovukLink>
    </div>
  )
}
