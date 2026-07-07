'use client'

import { Suspense, useState, ChangeEvent } from 'react'
import { Loader2 } from 'lucide-react'
import { UserRole, hasAnyRole } from '@/lib/utils'
import PaginatedUsers from '@/components/users/paginated-users'
import { useAuthorisedUser } from '@/hooks/use-authorised-user'
import { useOrganisation, useGetOrganisations } from '@/hooks/use-organisation'
import OrganisationOption from '@/components/organisation-options'
import { GovukBackLink, GovukButton, GovukButtonLink } from '@/components/govuk'
import { useRouter, useSearchParams } from 'next/navigation'
import { BannerNotification } from '@/components/banner-notification'
import { useInviteUserStore } from '@/stores/use-invite-user-store'

export default function UserManagementClient() {
  const router = useRouter()
  const searchParams = useSearchParams()

  const [selectedOrganisation, setSelectedOrganisation] = useState('')
  const { setInviteDetails } = useInviteUserStore()

  function getHref(page: number): string {
    const params = new URLSearchParams(searchParams.toString())
    params.set('page', String(page))
    return `?${params.toString()}`
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

  const { data: allOrganisations } = useGetOrganisations(isSystemAdmin)

  const handleOrganisationChange = (event: ChangeEvent<HTMLSelectElement>) => {
    const value = event.target.value
    setSelectedOrganisation(value)
    setInviteDetails('', '', value)
    router.replace(getHref(1))
  }

  const handleInviteUser = () => {
    router.push('/invite-user')
  }

  if (userLoading) return <Loader2 className="animate-spin" />

  if (userError) return <p>Error: Failed to load users.</p>

  return (
    <>
      <GovukBackLink />
      <BannerNotification />

      <h1 className="govuk-heading-l">User Management</h1>

      {isSystemAdmin && (
        <strong className="govuk-tag govuk-tag--grey">System Admin</strong>
      )}

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
              {allOrganisations &&
                allOrganisations.map((org) => (
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

      <div className="govuk-button-group">
        <GovukButton
          className="govuk-button"
          onClick={handleInviteUser}
          disabled={isSystemAdmin && !selectedOrganisation}
        >
          Invite new user
        </GovukButton>
        {hasAnyRole(currentUser?.roles, [UserRole.MHCLG_SUPPORT_ADMIN]) && (
          <GovukButtonLink
            href="/user-management/organisations/new"
            variant="secondary"
          >
            Create new organisation
          </GovukButtonLink>
        )}
      </div>

      {isSystemAdmin && (
        <>
          <hr className="govuk-section-break govuk-section-break--m govuk-section-break--visible" />

          <GovukButtonLink
            href="/user-management/organisations/domains"
            variant="secondary"
          >
            Edit approved domains
          </GovukButtonLink>
        </>
      )}

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
