import { useSearchParams } from 'next/navigation'

// Ensure the destination link is on this site
export const getSafeDestination = (destination: string): string | null => {
  try {
    const url = new URL(destination, window.location.origin)
    if (url.origin !== window.location.origin) return null
    return url.pathname + url.search + url.hash
  } catch {
    return null
  }
}

// Read the destination query param, falling back if it's missing or off-site
export const useDestination = (fallback: string) => {
  const destination = useSearchParams().get('destination')
  return (destination && getSafeDestination(destination)) ?? fallback
}
