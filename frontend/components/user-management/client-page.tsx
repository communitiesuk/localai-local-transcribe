'use client'

import { Suspense, useState, ChangeEvent } from 'react'
import { Loader2 } from 'lucide-react'
import { UserRole, hasAnyRole } from '@/lib/utils'
import PaginatedUsers from '@/components/users/paginated-users'
import { useAuthorisedUser } from '@/hooks/use-authorised-user'
import { useOrganisation, useGetOrganisations } from '@/hooks/use-organisation'
import OrganisationOption from '@/components/organisation-options'
import {
  GovukBackLink,
  GovukButton,
  GovukButtonLink,
  GovukTag,
  GovukHeading,
} from '@/components/govuk'
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

  console.log('DIAGNOSTIC isSystemAdmin:', isSystemAdmin, 'currentUser:', currentUser, 'allOrganisations:', allOrganisations)

  const handleOrganisationChange = (event: ChangeEvent<HTMLSelectElement>) => {
    const value = event.target.value
    setSelectedOrganisation(value)
    setInviteDetails('', '', value)
    router.replace(getHref(1))
  }

  const handleInviteUser = () => {
    router.push('/invite-user')
  }

  const handleEditDomains = () => {
    const orgId = isSystemAdmin
      ? selectedOrganisation
      : (organisation?.id ?? '')
    if (orgId) {
      router.push(`/user-management/organisations/${orgId}/domains`)
    }
  }

  if (userLoading) return <Loader2 className="animate-spin" />

  if (userError) return <p>Error: Failed to load users.</p>

  return (
    <>
      <GovukBackLink />
      <BannerNotification />

      <div className="flex items-baseline gap-4">
        <GovukHeading>User Management</GovukHeading>
        <GovukTag className="relative -top-px" colour="grey">
          System Admin
        </GovukTag>
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

      <hr className="govuk-section-break govuk-section-break--m govuk-section-break--visible" />

      <GovukButton
        onClick={handleEditDomains}
        variant="secondary"
        disabled={
          (isSystemAdmin && !selectedOrganisation) ||
          (!isSystemAdmin && !organisation)
        }
      >
        Edit approved domains
      </GovukButton>

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
