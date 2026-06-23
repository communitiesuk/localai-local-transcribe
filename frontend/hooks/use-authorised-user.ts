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

export function useAuthorisedOrgUser(organisationId?: string) {
  const {
    data: user,
    isLoading,
    isError,
  } = useQuery(getUserUsersMeGetOptions())

  let isAllowed: boolean | undefined // undefined if auth unknown

  if (user) {
    const isSystemAdmin = user.roles.includes(UserRole.MHCLG_SUPPORT_ADMIN)
    if (isSystemAdmin) {
      isAllowed = true
    } else if (organisationId !== undefined) {
      const isOrganisationAdmin =
        user.roles.includes(UserRole.LOCAL_AUTHORITY_ADMIN) &&
        user.organisation_id === organisationId
      isAllowed = isOrganisationAdmin
    } else {
      // data pending so isAllowed undefined
      isAllowed = undefined
    }
  }

  return {
    user,
    isLoading,
    isError,
    isAllowed,
  }
}
