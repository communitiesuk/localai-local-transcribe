'use client'

import { Button } from '@/components/ui/button'
import { ChevronLeft, Loader2 } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { useSystemUsers } from '@/hooks/use-users'
import { useQuery } from '@tanstack/react-query'
import { getUserUsersMeGetOptions } from '@/lib/client/@tanstack/react-query.gen'
import { useEffect } from 'react'
import { useState } from 'react'
import { USERS_PER_PAGE } from '@/lib/constants'

export default function UserManagementPage() {
  const router = useRouter()
  const [page, setPage] = useState(1)

  const { data: user, isLoading: userLoading } = useQuery(
    getUserUsersMeGetOptions()
  )
  const { data: usersResponse, isLoading: usersLoading } = useSystemUsers(
    page,
    USERS_PER_PAGE
  )

  const users = usersResponse?.items
  const totalPages = usersResponse?.total_pages

  const isAllowed = user?.roles?.some((role: string) =>
    ['local_authority_admin', 'mhclg_support_admin'].includes(role)
  )

  useEffect(() => {
    if (user && !isAllowed) {
      router.replace('/unauthorised')
    }
  }, [user, isAllowed, router])

  if (userLoading) return <Loader2 className="animate-spin" />
  if (user && !isAllowed) {
    return null
  }

  return (
    <div className="mx-auto max-w-3xl pt-1">
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
      <h1 className="text-3xl font-bold">User Management</h1>

      <div>
        <p className="govuk-body pt-5">
          {users && <> Total Users: {usersResponse.total_count}</>}
        </p>
      </div>

      <button type="submit" className="govuk-button" data-module="govuk-button">
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
              <th
                scope="col"
                className="govuk-table__header govuk-table__header"
              >
                Email
              </th>
              <th
                scope="col"
                className="govuk-table__header govuk-table__header--numeric"
              >
                {/* View Account placeholder */}
              </th>
            </tr>
          </thead>
          <tbody className="govuk-table__body">
            {users.map((user) => (
              <tr key={user.id} className="govuk-table__row">
                <th scope="row" className="govuk-table__header">
                  {user.name}
                </th>
                <td className="govuk-table__cell govuk-table__cell">
                  {user.email}
                </td>
                <td className="govuk-table__cell govuk-table__cell--numeric">
                  <div className="flex justify-end gap-3">
                    {user.roles.includes('local_authority_admin') && (
                      <strong className="govuk-tag">Admin</strong>
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
    </div>
  )
}
