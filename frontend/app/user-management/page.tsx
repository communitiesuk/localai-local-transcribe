'use client'

import { Suspense } from 'react'
import { GovukBackLink } from '@/components/govuk'
import { Loader2 } from 'lucide-react'
import Link from 'next/link'
import { UserRole, hasAnyRole } from '@/lib/utils'
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

  const isSystemAdmin = hasAnyRole(currentUser?.roles, [
    UserRole.MHCLG_SUPPORT_ADMIN,
  ])

  if (userLoading) return <Loader2 className="animate-spin" />

  if (userError) return <p>Error: Failed to load users.</p>

  return (
    <>
      <GovukBackLink />

      <h1 className="govuk-heading-l">User Management</h1>
      {organisation && <h2 className="govuk-heading-s">{organisation.name}</h2>}

      <div className="flex items-center gap-4">
        <button
          type="button"
          className="govuk-button"
          data-module="govuk-button"
        >
          Invite new user
        </button>
        {isSystemAdmin && (
          <Link
            href="/user-management/domains"
            className="govuk-link govuk-link--no-visited-state"
          >
            Edit approved domains
          </Link>
        )}
      </div>

      <Suspense fallback={null}>
        <PaginatedUsers />
      </Suspense>
    </>
  )
}
