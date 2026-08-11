import { useEffect, useRef } from 'react'

function animationInterval(
  ms: number,
  signal: AbortSignal,
  callback: (time: DOMHighResTimeStamp) => void
) {
  const start = performance.now()

  function frame(time: DOMHighResTimeStamp) {
    if (signal.aborted) return
    callback(time)
    scheduleFrame(time)
  }

  function scheduleFrame(time: DOMHighResTimeStamp) {
    const elapsed = time - start
    const roundedElapsed = Math.round(elapsed / ms) * ms
    const targetNext = start + roundedElapsed + ms
    const delay = targetNext - performance.now()

    window.setTimeout(() => {
      requestAnimationFrame(frame)
    }, delay)
  }

  scheduleFrame(start)
}

export const useAnimationFrame = (ms: number, callback: () => void) => {
  const callbackRef = useRef(callback)

  useEffect(() => {
    callbackRef.current = callback
  }, [callback])

  useEffect(() => {
    const controller = new AbortController()

    animationInterval(ms, controller.signal, () => callbackRef.current())

    return () => controller.abort()
  }, [ms])
}
