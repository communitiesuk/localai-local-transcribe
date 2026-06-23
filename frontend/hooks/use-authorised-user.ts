import { UserRole, hasAnyRole } from '@/lib/utils'
import { getUserUsersMeGetOptions } from '@/lib/client/@tanstack/react-query.gen'
import { useQuery } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'

export function useAuthorisedUser(allowedRoles: UserRole[]) {
  const router = useRouter()

  const {
    data: currentUser,
    isLoading,
    isError,
  } = useQuery(getUserUsersMeGetOptions())

  const isAllowed = hasAnyRole(currentUser?.roles, allowedRoles)

  useEffect(() => {
    if (currentUser && !isAllowed) {
      router.replace('/unauthorised')
    }
  }, [currentUser, isAllowed, router])

  return {
    currentUser,
    isAllowed,
    isLoading,
    isError,
  }
}
