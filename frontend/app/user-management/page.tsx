'use client'

import { Button } from '@/components/ui/button'
import { ChevronLeft } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { useUsers } from '@/hooks/use-users'
import { useQuery } from '@tanstack/react-query'
import { getUserUsersMeGetOptions } from '@/lib/client/@tanstack/react-query.gen'

export default function SupportPage() {
  const router = useRouter()
  const { data: user } = useQuery(getUserUsersMeGetOptions())
  const organisationId = user?.organisation_id ?? ''
  const { users } = useUsers(organisationId)

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
        <p class="govuk-body pt-5">
          Something Council <br />
          {users && <> Total Users: {users.length}</>}
        </p>
      </div>

      <button type="submit" class="govuk-button" data-module="govuk-button">
        Invite new user
      </button>

      {users && (
        <table class="govuk-table">
          <thead class="govuk-table__head">
            <tr class="govuk-table__row">
              <th scope="col" class="govuk-table__header">
                Name
              </th>
              <th scope="col" class="govuk-table__header govuk-table__header">
                Email
              </th>
              <th
                scope="col"
                class="govuk-table__header govuk-table__header--numeric"
              >
                {/* View Account placeholder */}
              </th>
            </tr>
          </thead>
          <tbody class="govuk-table__body">
            {users.map((user) => (
              <tr key={user.id} className="govuk-table__row">
                <th scope="row" class="govuk-table__header">
                  {user.name}
                </th>
                <td class="govuk-table__cell govuk-table__cell">
                  {user.email}
                </td>
                <td class="govuk-table__cell govuk-table__cell--numeric">
                  {user.roles.includes('local_authority_admin') && (
                    <strong class="govuk-tag">Admin</strong>
                  )}
                  <a
                    href="#"
                    class="govuk-link govuk-link--no-visited-state ml-5"
                  >
                    View Account
                  </a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
