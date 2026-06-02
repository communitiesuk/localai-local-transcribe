'use client'

import { Button } from '@/components/ui/button'
import { ChevronLeft } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { useOrgUsers, useSystemUsers } from '@/hooks/use-users'
import { useQuery } from '@tanstack/react-query'
import { getUserUsersMeGetOptions } from '@/lib/client/@tanstack/react-query.gen'

export default function SupportPage() {
  const router = useRouter()

  const { data: user } = useQuery(getUserUsersMeGetOptions())
  const { users, isLoading } = useOrgUsers(user?.organisation_id ?? '')

  // const { users, isLoading } = useSystemUsers()

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
          {users && <> Total Users: {users.length}</>}
        </p>
      </div>

      <button type="submit" className="govuk-button" data-module="govuk-button">
        Invite new user
      </button>

      {isLoading && <p>Loading</p>}

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
