'use client'

import Link from 'next/link'
import { GovukPagination } from '@/components/govuk/pagination'
import { USERS_PER_PAGE } from '@/lib/constants'
import { useSearchParams } from 'next/navigation'
import { UserRole, hasAnyRole } from '@/lib/utils'
import { Loader2 } from 'lucide-react'
import {
  GovukTable,
  GovukTableHead,
  GovukTableBody,
  GovukTableRow,
  GovukTableCell,
  GovukTableHeaderCell,
} from '@/components/govuk/table'
import {
  listOrganisationsUsersOrganisationsOrganisationIdUsersGetOptions,
  listUsersUsersGetOptions,
} from '@/lib/client/@tanstack/react-query.gen'
import { useQuery } from '@tanstack/react-query'

type Props = {
  organisationID: string
  isSystemAdmin: boolean
  getHref: (page: number) => string
}

export default function PaginatedUsers({
  organisationID,
  isSystemAdmin,
  getHref,
}: Props) {
  const hasSelectedOrganisation = organisationID !== ''
  const searchParams = useSearchParams()
  const currentPage = Number(searchParams.get('page') ?? '1')

  const localAdminQuery = useQuery({
    ...listUsersUsersGetOptions({
      query: {
        page: currentPage,
        page_size: USERS_PER_PAGE,
      },
    }),
    enabled: !isSystemAdmin,
  })

  const sysAdminQuery = useQuery({
    ...listOrganisationsUsersOrganisationsOrganisationIdUsersGetOptions({
      path: {
        organisation_id: organisationID,
      },
      query: {
        page: currentPage,
        page_size: USERS_PER_PAGE,
      },
    }),
    enabled: isSystemAdmin && hasSelectedOrganisation,
  })

  const activeQuery = isSystemAdmin ? sysAdminQuery : localAdminQuery
  const {
    data: {
      items: users,
      total_pages: totalPages,
      total_count: totalCount,
    } = {},
    isLoading,
    error,
  } = activeQuery

  if (error) return <p>Error: Failed to load users.</p>

  return (
    <>
      {isLoading && <Loader2 className="animate-spin" />}

      <p className="govuk-body">Total Users: {totalCount ?? 0}</p>

      <GovukTable>
        <GovukTableHead>
          <GovukTableRow>
            <GovukTableHeaderCell>Name</GovukTableHeaderCell>
            <GovukTableHeaderCell>Email</GovukTableHeaderCell>
            <GovukTableHeaderCell>
              &nbsp; {/* View Account placeholder column */}
            </GovukTableHeaderCell>
          </GovukTableRow>
        </GovukTableHead>
        <GovukTableBody>
          {isSystemAdmin && !hasSelectedOrganisation ? (
            <GovukTableRow>
              <GovukTableCell colSpan={3}>
                Please select an organisation to view associated users.
              </GovukTableCell>
            </GovukTableRow>
          ) : (
            users?.map((user) => (
              <GovukTableRow key={user.id}>
                <GovukTableCell>{user.name}</GovukTableCell>
                <GovukTableCell>{user.email}</GovukTableCell>
                <GovukTableCell>
                  <div className="flex justify-end gap-3">
                    {!user?.is_active && (
                      <strong className="govuk-tag govuk-tag--red">
                        Inactive
                      </strong>
                    )}
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
                    <Link
                      href={`/user-management/users/${user?.id}`}
                      className="govuk-link govuk-link--no-visited-state"
                    >
                      View Account
                    </Link>
                  </div>
                </GovukTableCell>
              </GovukTableRow>
            ))
          )}
        </GovukTableBody>
      </GovukTable>

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
