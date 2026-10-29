'use client'

import { useEffect, useState } from 'react'

import { GovukBody, GovukButton } from '@/components/govuk'

export function RecordingLoading({
  onComplete,
  onCancel,
}: {
  onComplete: () => void
  onCancel: () => void
}) {
  const [countdown, setCountdown] = useState(3)

  useEffect(() => {
    if (countdown === 0) {
      onComplete()
      return
    }

    const timeoutId = window.setTimeout(() => {
      setCountdown((currentCountdown) => currentCountdown - 1)
    }, 1000)

    return () => window.clearTimeout(timeoutId)
  }, [countdown, onComplete])

  return (
    <div className="govuk-!-text-align-centre">
      <GovukBody size="l">Recording starts in&hellip;</GovukBody>
      <p className="mb-7 text-5xl font-bold">{countdown}</p>
      <GovukButton onClick={onCancel} variant="link">
        Cancel
      </GovukButton>
    </div>
  )
}
