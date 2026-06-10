'use client'

import { Button } from '@/components/ui/button'
import { ChevronLeft, Loader2 } from 'lucide-react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useUsers } from '@/hooks/use-users'
import { useQuery } from '@tanstack/react-query'
import {
  getUserUsersMeGetOptions,
  getOrganisationOrganisationsOrganisationIdGetOptions,
} from '@/lib/client/@tanstack/react-query.gen'
import { useEffect } from 'react'
import { USERS_PER_PAGE } from '@/lib/constants'
import { UserRole, hasAnyRole } from '@/lib/utils'
import { GovukPagination } from '@/components/govuk/pagination'

export default function UserManagementPage() {
  const router = useRouter()
  const searchParams = useSearchParams()

  function getHref(page: number) {
    const params = new URLSearchParams(searchParams.toString())
    params.set('page', String(page))
    return `?${params.toString()}`
  }

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

  const currentPage = Number(searchParams.get('page') ?? '1')

  const {
    data: usersResponse,
    isLoading: usersLoading,
    isError: usersError,
  } = useUsers(currentPage, USERS_PER_PAGE)
  const users = usersResponse?.items
  const totalPages = usersResponse?.total_pages

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

  if (userError || usersError) return <p>Error: Failed to load users.</p>

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

      {users && (
        <p className="govuk-body">Total Users: {usersResponse.total_count}</p>
      )}

      <button type="button" className="govuk-button" data-module="govuk-button">
        Invite new user
      </button>

      {usersLoading && <Loader2 className="animate-spin" />}

      {users && (
        <table className="govuk-table">
          <thead className="govuk-table__head">
            <tr className="govuk-table__row">
              <th scope="col" className="govuk-table__header">
                Name
              </th>
              <th scope="col" className="govuk-table__header">
                Email
              </th>
              <th
                scope="col"
                className="govuk-table__header govuk-table__header--numeric"
              >
                {/* View Account placeholder column */}
              </th>
            </tr>
          </thead>
          <tbody className="govuk-table__body">
            {users.map((user) => (
              <tr key={user.id} className="govuk-table__row">
                <td scope="row" className="govuk-table__cell">
                  {user.name}
                </td>
                <td className="govuk-table__cell">{user.email}</td>
                <td className="govuk-table__cell govuk-table__cell--numeric">
                  <div className="flex justify-end gap-3">
                    {hasAnyRole(user?.roles, [
                      UserRole.LOCAL_AUTHORITY_ADMIN,
                    ]) && <strong className="govuk-tag">LA Admin</strong>}
                    {hasAnyRole(user?.roles, [
                      UserRole.MHCLG_SUPPORT_ADMIN,
                    ]) && (
                      <strong className="govuk-tag govuk-tag--purple">
                        System Admin
                      </strong>
                    )}
                    <a
                      href="#"
                      className="govuk-link govuk-link--no-visited-state"
                    >
                      View Account
                    </a>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {(totalPages ?? 0) > 1 && (
        <GovukPagination
          currentPage={currentPage}
          totalPages={totalPages!}
          getHref={getHref}
        />
      )}
    </>
  )
}
