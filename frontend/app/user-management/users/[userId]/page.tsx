'use client'

import { use } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'

import { GovukHeading, GovukButton } from '@/components/govuk'
import {
  GovukTable,
  GovukTableBody,
  GovukTableRow,
  GovukTableCell,
  GovukTableHeaderCell,
} from '@/components/govuk/table'
import {
  getTargetUserUsersUserIdGetOptions,
  deleteUserUsersUserIdDeleteMutation,
} from '@/lib/client/@tanstack/react-query.gen'

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

  const { mutate: deleteUser } = useMutation(
    deleteUserUsersUserIdDeleteMutation()
  )

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

      <GovukButton
        variant="warning"
        onClick={() => deleteUser({ path: { user_id: userId } })}
      >
        Delete account
      </GovukButton>
    </>
  )
}
