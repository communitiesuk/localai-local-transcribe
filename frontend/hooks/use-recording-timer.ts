import { useEffect, useRef } from 'react'

export const useRecordingTimer = (
  ms: number,
  callback: (elapsedMs: number) => void
) => {
  const callbackRef = useRef(callback)
  const previousTickRef = useRef<number | null>(null)

  useEffect(() => {
    callbackRef.current = callback
  }, [callback])

  useEffect(() => {
    previousTickRef.current = Date.now()

    const intervalId = window.setInterval(() => {
      const now = Date.now()
      const previousTick = previousTickRef.current ?? now

      previousTickRef.current = now
      callbackRef.current(now - previousTick)
    }, ms)

    return () => {
      previousTickRef.current = null
      window.clearInterval(intervalId)
    }
  }, [ms])
}
