import { useLockNavigationContext } from '@/hooks/use-lock-navigation-context'
import { useEffect } from 'react'

export const useTabCloseWarning = (shouldPreventClose: boolean | string) => {
  const { setLockNavigation } = useLockNavigationContext()
  useEffect(() => {
    if (shouldPreventClose) {
      setLockNavigation(shouldPreventClose)
    }
    return () => {
      setLockNavigation(false)
    }
  }, [shouldPreventClose, setLockNavigation])
}
