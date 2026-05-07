import * as React from 'react'

const MOBILE_BREAKPOINT = 768

export function useIsMobile() {
  const [isMobile, setIsMobile] = React.useState(false)

  React.useEffect(() => {
    const mql = window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT - 1}px)`)
    
    // Define a handler function
    const handleMatchChange = (e: MediaQueryListEvent) => {
      setIsMobile(e.matches)
    }

    // Set initial state
    setIsMobile(mql.matches)

    // Add listener
    mql.addEventListener('change', handleMatchChange)

    // Cleanup
    return () => mql.removeEventListener('change', handleMatchChange)
  }, [])

  return isMobile
}