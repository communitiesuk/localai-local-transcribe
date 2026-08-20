'use client'

import { useCallback, useState } from 'react'

type UseCountdownOptions = {
  onComplete: () => Promise<void> | void
  onCancel: () => void
}

export function useCountdown({ onComplete, onCancel }: UseCountdownOptions) {
  const [isStartingRecording, setIsStartingRecording] = useState(false)
  const [isPreparingRecording, setIsPreparingRecording] = useState(false)

  const startCountdown = useCallback(() => {
    setIsStartingRecording(true)
  }, [])

  const handleLoadingComplete = useCallback(async () => {
    setIsStartingRecording(false)
    setIsPreparingRecording(true)

    try {
      await onComplete()
    } finally {
      setIsPreparingRecording(false)
    }
  }, [onComplete])

  const handleLoadingCancel = useCallback(() => {
    setIsStartingRecording(false)
    onCancel()
  }, [onCancel])

  return {
    isStartingRecording,
    isPreparingRecording,
    startCountdown,
    handleLoadingComplete,
    handleLoadingCancel,
  }
}
