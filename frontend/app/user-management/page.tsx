'use client'

import { Suspense } from 'react'
import { Button } from '@/components/ui/button'
import { ChevronLeft, Loader2 } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import {
  getUserUsersMeGetOptions,
  getOrganisationOrganisationsOrganisationIdGetOptions,
} from '@/lib/client/@tanstack/react-query.gen'
import { useEffect } from 'react'
import { UserRole, hasAnyRole } from '@/lib/utils'
import PaginatedUsers from '@/components/users/paginated-users'

export default function UserManagementPage() {
  const router = useRouter()

  const {
    data: currentUser,
    isLoading: userLoading,
    isError: userError,
  } = useQuery(getUserUsersMeGetOptions())

  const organisationId = currentUser?.organisation_id
  const { data: organisation } = useQuery({
    ...getOrganisationOrganisationsOrganisationIdGetOptions({
      path: {
        organisation_id: organisationId!, // wont be undefined due to enabled
      },
    }),
    enabled: !!organisationId,
  })

  const isAllowed = hasAnyRole(currentUser?.roles, [
    UserRole.LOCAL_AUTHORITY_ADMIN,
    UserRole.MHCLG_SUPPORT_ADMIN,
  ])

  useEffect(() => {
    if (currentUser && !isAllowed) {
      router.replace('/unauthorised')
    }
  }, [currentUser, isAllowed, router])

  if (userLoading) return <Loader2 className="animate-spin" />

  if (userError) return <p>Error: Failed to load users.</p>

  return (
    <>
      <Button
        variant="link"
        className="mb-4 self-start px-0! underline hover:decoration-2"
        onClick={() => {
          router.back()
        }}
      >
        <span className="flex items-center">
          <ChevronLeft />
          Back
        </span>
      </Button>

      <h1 className="govuk-heading-l">User Management</h1>
      {organisation && <h2 className="govuk-heading-s">{organisation.name}</h2>}

      <button type="button" className="govuk-button" data-module="govuk-button">
        Invite new user
      </button>

      <Suspense fallback={null}>
        <PaginatedUsers />
      </Suspense>
    </>
  )
}
