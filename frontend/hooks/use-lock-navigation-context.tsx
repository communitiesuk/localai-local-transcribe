'use client'

import {
  createContext,
  Dispatch,
  SetStateAction,
  useContext,
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
