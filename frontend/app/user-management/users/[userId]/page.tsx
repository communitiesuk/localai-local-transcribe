'use client'

import { use } from 'react'
import { useQuery } from '@tanstack/react-query'

import { GovukHeading } from '@/components/govuk'
import {
  GovukTable,
  GovukTableBody,
  GovukTableRow,
  GovukTableCell,
  GovukTableHeaderCell,
} from '@/components/govuk/table'
import { getTargetUserUsersUserIdGetOptions } from '@/lib/client/@tanstack/react-query.gen'

export default function UserPage(props: {
  params: Promise<{ userId: string }>
}) {
  const { userId } = use(props.params)

  const userResponse = useQuery({
    ...getTargetUserUsersUserIdGetOptions({
      path: {
        user_id: userId,
      },
    }),
  })

  return (
    <>
      <GovukHeading>Edit user permissions</GovukHeading>

      <div>
        <GovukTable>
          <GovukTableBody>
            <GovukTableRow>
              <GovukTableHeaderCell>Name</GovukTableHeaderCell>
              <GovukTableCell>{userResponse.data?.name}</GovukTableCell>
            </GovukTableRow>
            <GovukTableRow>
              <GovukTableHeaderCell>Email address</GovukTableHeaderCell>
              <GovukTableCell>{userResponse.data?.email}</GovukTableCell>
            </GovukTableRow>
          </GovukTableBody>
        </GovukTable>
      </div>
    </>
  )
}
