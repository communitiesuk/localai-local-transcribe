'use client'

import { Button } from '@/components/ui/button'
import { ChevronLeft, Loader2 } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { useUsers } from '@/hooks/use-users'
import { useQuery } from '@tanstack/react-query'
import {
  getUserUsersMeGetOptions,
  getOrganisationOrganisationsOrganisationIdGetOptions,
} from '@/lib/client/@tanstack/react-query.gen'
import { useState, useEffect } from 'react'
import { USERS_PER_PAGE } from '@/lib/constants'
import { userRoles, hasAnyRole } from '@/lib/utils'

export default function UserManagementPage() {
  const router = useRouter()

  const { data: user, isLoading: userLoading } = useQuery(
    getUserUsersMeGetOptions()
  )

  const organisationId = user?.organisation_id
  const { data: organisation } = useQuery({
    ...getOrganisationOrganisationsOrganisationIdGetOptions({
      path: {
        organisation_id: organisationId!, // wont be undefined due to enabled
      },
    }),
    enabled: !!organisationId,
  })

  const [currentPage, setCurrentPage] = useState(1)
  const { data: usersResponse, isLoading: usersLoading } = useUsers(
    currentPage,
    USERS_PER_PAGE
  )
  const users = usersResponse?.items
  const totalPages = usersResponse?.total_pages

  const isAllowed = hasAnyRole(user?.roles, [
    userRoles.LOCAL_AUTHORITY_ADMIN,
    userRoles.MHCLG_SUPPORT_ADMIN,
  ])

  useEffect(() => {
    if (user && !isAllowed) {
      router.replace('/unauthorised')
    }
  }, [user, isAllowed, router])

  if (userLoading) return <Loader2 className="animate-spin" />

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

      <h1 className="govuk-heading-l">User Management</h1>
      {organisation && <h2 className="govuk-heading-s">{organisation.name}</h2>}

      {users && (
        <p className="govuk-body">Total Users: {usersResponse.total_count}</p>
      )}

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
                      userRoles.LOCAL_AUTHORITY_ADMIN,
                    ]) && <strong className="govuk-tag">LA Admin</strong>}
                    {hasAnyRole(user?.roles, [
                      userRoles.MHCLG_SUPPORT_ADMIN,
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
        <nav className="govuk-pagination" aria-label="Pagination">
          <div className="govuk-pagination__prev">
            {currentPage !== 1 && (
              <a
                className="govuk-link govuk-pagination__link"
                rel="prev"
                onClick={(e) => {
                  e.preventDefault()
                  setCurrentPage(currentPage - 1)
                }}
              >
                <svg
                  className="govuk-pagination__icon govuk-pagination__icon--prev"
                  xmlns="http://www.w3.org/2000/svg"
                  height="13"
                  width="15"
                  aria-hidden="true"
                  focusable="false"
                  viewBox="0 0 15 13"
                >
                  <path d="m6.5938-0.0078125-6.7266 6.7266 6.7441 6.4062 1.377-1.449-4.1856-3.9768h12.896v-2h-12.984l4.2931-4.293-1.414-1.414z"></path>
                </svg>
                <span className="govuk-pagination__link-title">
                  Previous<span className="govuk-visually-hidden"> page</span>
                </span>
              </a>
            )}
          </div>
          <ul className="govuk-pagination__list">
            {Array.from({ length: totalPages ?? 0 }, (_, index) => {
              const page = index + 1
              const isCurrent = page === currentPage

              return (
                <li
                  key={page}
                  className={`govuk-pagination__item ${
                    isCurrent ? 'govuk-pagination__item--current' : ''
                  }`}
                >
                  <a
                    className="govuk-link govuk-pagination__link"
                    href="#"
                    aria-label={`Page ${page}`}
                    aria-current={isCurrent ? 'page' : undefined}
                    onClick={(e) => {
                      e.preventDefault()
                      setCurrentPage(page)
                    }}
                  >
                    {page}
                  </a>
                </li>
              )
            })}
          </ul>
          <div className="govuk-pagination__next">
            {currentPage !== totalPages && (
              <a
                className="govuk-link govuk-pagination__link"
                rel="next"
                onClick={(e) => {
                  e.preventDefault()
                  setCurrentPage(currentPage + 1)
                }}
              >
                <span className="govuk-pagination__link-title">
                  Next<span className="govuk-visually-hidden"> page</span>
                </span>
                <svg
                  className="govuk-pagination__icon govuk-pagination__icon--next"
                  xmlns="http://www.w3.org/2000/svg"
                  height="13"
                  width="15"
                  aria-hidden="true"
                  focusable="false"
                  viewBox="0 0 15 13"
                >
                  <path d="m8.107-0.0078125-1.4136 1.414 4.2926 4.293h-12.986v2h12.896l-4.1855 3.9766 1.377 1.4492 6.7441-6.4062-6.7246-6.7266z"></path>
                </svg>
              </a>
            )}
          </div>
        </nav>
      )}
    </div>
  )
}
