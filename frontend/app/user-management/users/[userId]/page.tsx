'use client'

import { use, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'

import {
  GovukHeading,
  GovukButtonLink,
  GovukBackLink,
} from '@/components/govuk'
import {
  GovukTable,
  GovukTableBody,
  GovukTableRow,
  GovukTableCell,
  GovukTableHeaderCell,
} from '@/components/govuk/table'
import { getTargetUserUsersUserIdGetOptions } from '@/lib/client/@tanstack/react-query.gen'
import { useAuthorisedOrgUser } from '@/hooks/use-authorised-user'
import { useRouter } from 'next/navigation'
import { Loader2 } from 'lucide-react'

export default function UserPage(props: {
  params: Promise<{ userId: string }>
}) {
  const router = useRouter()

  const { userId } = use(props.params)

  const {
    data: targetUser,
    isLoading: targetUserLoading,
    isError: targetUserError,
  } = useQuery({
    ...getTargetUserUsersUserIdGetOptions({
      path: {
        user_id: userId,
      },
    }),
  })

  const {
    isAllowed,
    isLoading: authLoading,
    isError: authError,
  } = useAuthorisedOrgUser(targetUser?.organisation_id ?? undefined)

  const authReady = !targetUserLoading && !authLoading
  const pageError = targetUserError || authError

  useEffect(() => {
    if (pageError) {
      router.replace('/generic-error')
    }

    if (authReady && isAllowed === false) {
      router.replace('/unauthorised')
    }
  }, [pageError, authReady, isAllowed, router])

  if (targetUserLoading || authLoading) {
    return <Loader2 className="animate-spin" />
  }

  if (pageError) return null

  return (
    <>
      <GovukBackLink href="/user-management" />
      <GovukHeading>Edit user permissions</GovukHeading>

      <div>
        <GovukTable>
          <GovukTableBody>
            <GovukTableRow>
              <GovukTableHeaderCell>Name</GovukTableHeaderCell>
              <GovukTableCell>{targetUser?.name}</GovukTableCell>
            </GovukTableRow>
            <GovukTableRow>
              <GovukTableHeaderCell>Email address</GovukTableHeaderCell>
              <GovukTableCell>{targetUser?.email}</GovukTableCell>
            </GovukTableRow>
          </GovukTableBody>
        </GovukTable>
      </div>

      <GovukButtonLink
        variant="warning"
        href={`/user-management/users/${userId}/delete`}
      >
        Delete account
      </GovukButtonLink>
    </>
  )
}
