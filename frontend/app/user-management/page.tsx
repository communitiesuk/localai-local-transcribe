'use client'

import { Suspense } from 'react'
import { Button } from '@/components/ui/button'
import { ChevronLeft, Loader2 } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { UserRole } from '@/lib/utils'
import PaginatedUsers from '@/components/users/paginated-users'
import { useAuthorisedUser } from '@/hooks/use-authorised-user'
import { useOrganisation } from '@/hooks/use-organisation'

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

      <button
        type="button"
        className="govuk-button"
        data-module="govuk-button"
        onClick={() => router.push('/invite-user')}
      >
        Invite new user
      </button>

      <Suspense fallback={null}>
        <PaginatedUsers />
      </Suspense>
    </>
  )
}
