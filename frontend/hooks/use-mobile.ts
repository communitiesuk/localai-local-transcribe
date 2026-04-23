import * as React from 'react'

const MOBILE_BREAKPOINT = 768

export function useIsMobile() {
  // Initialize state based on window width immediately if window exists
  // This avoids the need to call setIsMobile synchronously inside useEffect
  const [isMobile, setIsMobile] = React.useState<boolean>(() => {
    if (typeof window === 'undefined') return false
    return window.innerWidth < MOBILE_BREAKPOINT
  })

  React.useEffect(() => {
    const mql = window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT - 1}px)`)

    const onChange = () => {
      // Use the matches property from the event/mql for better accuracy
      setIsMobile(window.innerWidth < MOBILE_BREAKPOINT)
    }

    mql.addEventListener('change', onChange)

    // We remove the synchronous setIsMobile call from here
    // because the initial state is already set above.

    return () => mql.removeEventListener('change', onChange)
  }, [])

  return !!isMobile
}
