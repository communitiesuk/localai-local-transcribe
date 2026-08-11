const [count, setCount] = useState(0)

function animationInterval(ms, signal, callback) {
  const start = document.timeline
    ? document.timeline.currentTime
    : performance.now()

  function frame(time) {
    if (signal.aborted) return
    callback(time)
    scheduleFrame(time)
  }

  function scheduleFrame(time) {
    const elapsed = time - start
    const roundedElapsed = Math.round(elapsed / ms) * ms
    const targetNext = start + roundedElapsed + ms
    const delay = targetNext - performance.now()
    setTimeout(() => requestAnimationFrame(frame), delay)
  }

  scheduleFrame(start)
}

const useAnimationFrame = (ms, callback) => {
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

useAnimationFrame(1000, () => {
  if (isPaused) return
  setCount((count) => count + 1)
})
