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

  useEffect(() => {
    if (targetUserError) {
      router.replace('/generic-error')
    }
  }, [targetUserError, router])

  if (targetUserLoading) {
    return <Loader2 className="animate-spin" />
  }

  if (targetUserError) return null

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
