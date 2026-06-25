'use client'

import { Suspense, useState } from 'react'
import { Button } from '@/components/ui/button'
import { ChevronLeft, Loader2 } from 'lucide-react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { UserRole, hasAnyRole } from '@/lib/utils'
import PaginatedUsers from '@/components/users/paginated-users'
import { useAuthorisedUser } from '@/hooks/use-authorised-user'
import { useOrganisation, useGetOrganisations } from '@/hooks/use-organisation'
import OrganisationOption from '@/components/organisation-options'

export default function UserManagementPage() {
  const router = useRouter()
  const [selectedOrganisation, setSelectedOrganisation] = useState('')

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

  const { data: allOrganistions } = useGetOrganisations(isSystemAdmin)
  const numberOfOrgs = allOrganistions?.length ?? 0

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

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <h1 className="govuk-heading-l govuk-!-margin-bottom-0">
          User Management
        </h1>

        {isSystemAdmin && (
          <strong className="govuk-tag govuk-tag--grey">System Admin</strong>
        )}
      </div>
      {isSystemAdmin && (
        <>
          <div className="govuk-form-group govuk-!-padding-top-1">
            <label className="govuk-label" htmlFor="sortOrgs">
              Selected council:
            </label>
            <select
              className="govuk-select"
              id="sortOrgs"
              name="sortOrgs"
              value={selectedOrganisation}
              onChange={(e) => setSelectedOrganisation(e.target.value)}
            >
              <option value="" disabled>
                Select Organisation
              </option>
              {allOrganistions &&
                allOrganistions.map((org) => (
                  <OrganisationOption
                    key={org.id}
                    id={org.id}
                    name={org.name}
                  />
                ))}
            </select>
          </div>

          <div>Total accounts: {numberOfOrgs}</div>
        </>
      )}

      {!isSystemAdmin && organisation && (
        <h2 className="govuk-heading-s">{organisation.name}</h2>
      )}

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
        <PaginatedUsers organisationID={selectedOrganisation} />
      </Suspense>
    </>
  )
}
