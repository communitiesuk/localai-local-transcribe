'use client'

import {
  createContext,
  Dispatch,
  SetStateAction,
  useContext,
  useEffect,
  useState,
} from 'react'

type LockNavigationContextType = {
  lockNavigation: boolean | string | ((href: string) => void)
  setLockNavigation: Dispatch<
    SetStateAction<boolean | string | ((href: string) => void)>
  >
}

const LockNavigationContext = createContext<LockNavigationContextType>({
  lockNavigation: false,
  setLockNavigation: () => {},
})

export const LockNavigationProvider = ({
  children,
}: {
  children: React.ReactNode
}) => {
  const [lockNavigation, setLockNavigation] = useState<
    string | boolean | ((href: string) => void)
  >(false)

  useEffect(() => {
    if (!lockNavigation) return

    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      e.preventDefault()
      e.returnValue = true
    }
    window.addEventListener('beforeunload', handleBeforeUnload)

    const handleNavigate = (e: NavigateEvent) => {
      if (typeof lockNavigation !== 'function') return
      if (e.navigationType !== 'traverse' || !e.cancelable) return
      e.preventDefault()
      const { pathname, search } = new URL(e.destination.url)
      lockNavigation(pathname + search)
    }
    window.navigation?.addEventListener('navigate', handleNavigate)

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload)
      window.navigation?.removeEventListener('navigate', handleNavigate)
    }
  }, [lockNavigation])

  return (
    <LockNavigationContext.Provider
      value={{ lockNavigation, setLockNavigation }}
    >
      {children}
    </LockNavigationContext.Provider>
  )
}

export const useLockNavigationContext = () => {
  return useContext(LockNavigationContext)
}

export const useLockNavigation = (
  lock: LockNavigationContextType['lockNavigation']
) => {
  const { setLockNavigation } = useLockNavigationContext()
  useEffect(() => {
    if (lock) {
      setLockNavigation(() => lock)
    }
    return () => {
      setLockNavigation(false)
    }
  }, [lock, setLockNavigation])
}
