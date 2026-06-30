'use client'

import { Suspense } from 'react'
import { Loader2 } from 'lucide-react'
import { UserRole, hasAnyRole } from '@/lib/utils'
import PaginatedUsers from '@/components/users/paginated-users'
import { useAuthorisedUser } from '@/hooks/use-authorised-user'
import { useOrganisation } from '@/hooks/use-organisation'
import { GovukButtonLink, GovukButton, GovukBackLink } from '@/components/govuk'
import { BannerNotification } from '@/components/banner-notification'

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

      <BannerNotification />

      <h1 className="govuk-heading-l">User Management</h1>
      {organisation && <h2 className="govuk-heading-s">{organisation.name}</h2>}

      <div className="govuk-button-group">
        <GovukButton>Invite new user</GovukButton>

        {hasAnyRole(currentUser?.roles, [UserRole.MHCLG_SUPPORT_ADMIN]) && (
          <GovukButtonLink href="/organisations/new" variant="secondary">
            Create new organisation
          </GovukButtonLink>
        )}
      </div>

      {isSystemAdmin && (
        <>
          <hr className="govuk-section-break govuk-section-break--m govuk-section-break--visible" />

          <GovukButtonLink href="/user-management/domains" variant="secondary">
            Edit approved domains
          </GovukButtonLink>
        </>
      )}

      <Suspense fallback={null}>
        <PaginatedUsers />
      </Suspense>
    </>
  )
}
