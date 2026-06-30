'use client'

import { Suspense, useState, ChangeEvent } from 'react'
import { Loader2 } from 'lucide-react'
import Link from 'next/link'
import { UserRole, hasAnyRole } from '@/lib/utils'
import PaginatedUsers from '@/components/users/paginated-users'
import { useAuthorisedUser } from '@/hooks/use-authorised-user'
import { useOrganisation, useGetOrganisations } from '@/hooks/use-organisation'
import OrganisationOption from '@/components/organisation-options'
import { GovukBackLink } from '@/components/govuk'
import { useRouter, useSearchParams } from 'next/navigation'
import { BannerNotification } from '@/components/banner-notification'

export default function UserManagementPage() {
  const router = useRouter()
  const searchParams = useSearchParams()

  const [selectedOrganisation, setSelectedOrganisation] = useState('')

  function buildPageUrl(page: number): string {
    const params = new URLSearchParams(searchParams.toString())
    params.set('page', String(page))
    return `?${params.toString()}`
  }

  function getHref(page: number): string {
    return buildPageUrl(page)
  }

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

  const handleOrganisationChange = (event: ChangeEvent<HTMLSelectElement>) => {
    const value = event.target.value
    setSelectedOrganisation(value)
    router.replace(buildPageUrl(1))
  }

  if (userLoading) return <Loader2 className="animate-spin" />

  if (userError) return <p>Error: Failed to load users.</p>

  return (
    <>
      <GovukBackLink />
      <BannerNotification/>

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
              onChange={handleOrganisationChange}
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
        <PaginatedUsers
          organisationID={
            isSystemAdmin ? selectedOrganisation : (organisation?.id ?? '')
          }
          isSystemAdmin={isSystemAdmin}
          getHref={getHref}
        />
      </Suspense>
    </>
  )
}
