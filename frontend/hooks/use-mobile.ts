import * as React from 'react'

const MOBILE_BREAKPOINT = 768
const mobileMediaQuery = `(max-width: ${MOBILE_BREAKPOINT - 1}px)`

export function useIsMobile() {
  const [isMobile, setIsMobile] = React.useState<boolean | undefined>(() =>
    typeof window !== 'undefined'
      ? window.matchMedia(mobileMediaQuery).matches
      : undefined
  )

  React.useEffect(() => {
    const mql = window.matchMedia(mobileMediaQuery)

    const onChange = (e: MediaQueryListEvent) => {
      setIsMobile(e.matches)
    }

    mql.addEventListener('change', onChange)

    return () => mql.removeEventListener('change', onChange)
  }, [])

  return !!isMobile
}
