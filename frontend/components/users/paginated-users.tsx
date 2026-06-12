'use client'

import Link from 'next/link'
import { useUsers } from '@/hooks/use-users'
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

export default function PaginatedUsers() {
  const searchParams = useSearchParams()
  const currentPage = Number(searchParams.get('page') ?? '1')

  function getHref(page: number) {
    const params = new URLSearchParams(searchParams.toString())
    params.set('page', String(page))
    return `?${params.toString()}`
  }

  const {
    data: usersResponse,
    isLoading: usersLoading,
    isError: usersError,
  } = useUsers(currentPage, USERS_PER_PAGE)

  const users = usersResponse?.items
  const totalPages = usersResponse?.total_pages

  if (usersError) return <p>Error: Failed to load users.</p>

  return (
    <>
      {usersLoading && <Loader2 className="animate-spin" />}

      <p className="govuk-body">Total Users: {usersResponse?.total_count}</p>

      {users && (
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
            {users.map((user) => (
              <GovukTableRow key={user.id}>
                <GovukTableCell>{user.name}</GovukTableCell>
                <GovukTableCell>{user.email}</GovukTableCell>
                <GovukTableCell>
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
                    <Link
                      href="#"
                      className="govuk-link govuk-link--no-visited-state"
                    >
                      View Account
                    </Link>
                  </div>
                </GovukTableCell>
              </GovukTableRow>
            ))}
          </GovukTableBody>
        </GovukTable>
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
