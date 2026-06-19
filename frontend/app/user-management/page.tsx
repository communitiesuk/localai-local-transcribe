'use client'

import { Suspense } from 'react'
import { Button } from '@/components/ui/button'
import { ChevronLeft, Loader2 } from 'lucide-react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { UserRole, hasAnyRole } from '@/lib/utils'
import PaginatedUsers from '@/components/users/paginated-users'
import { useAuthorisedUser } from '@/hooks/use-authorised-user'
import { useOrganisation } from '@/hooks/use-organisation'
import { GovukButtonLink, GovukButton } from '@/components/govuk'

export default function UserManagementPage() {
  const router = useRouter()

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

      <div className="flex gap-5">
        <GovukButton>Invite new user</GovukButton>

        {hasAnyRole(currentUser?.roles, [UserRole.MHCLG_SUPPORT_ADMIN]) && (
          <GovukButtonLink href="/organisations/new" variant="secondary">
            Create new organisation
          </GovukButtonLink>
        )}
      </div>

      {isSystemAdmin && (
        <GovukButtonLink href="/user-management/domains" variant="secondary">
          Edit approved domains
        </GovukButtonLink>
      )}

      <Suspense fallback={null}>
        <PaginatedUsers />
      </Suspense>
    </>
  )
}
