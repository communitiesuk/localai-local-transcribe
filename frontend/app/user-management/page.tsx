'use client'

import { Suspense } from 'react'
import { GovukBackLink } from '@/components/govuk'
import { Loader2 } from 'lucide-react'
import { UserRole } from '@/lib/utils'
import PaginatedUsers from '@/components/users/paginated-users'
import { useAuthorisedUser } from '@/hooks/use-authorised-user'
import { useOrganisation } from '@/hooks/use-organisation'

export default function UserManagementPage() {
  const {
    currentUser,
    isLoading: userLoading,
    isError: userError,
  } = useAuthorisedUser([
    UserRole.LOCAL_AUTHORITY_ADMIN,
    UserRole.MHCLG_SUPPORT_ADMIN,
  ])

  const { data: organisation } = useOrganisation(
    currentUser?.organisation_id ?? ''
  )

  if (userLoading) return <Loader2 className="animate-spin" />

  if (userError) return <p>Error: Failed to load users.</p>

  return (
    <>
      <GovukBackLink />

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
