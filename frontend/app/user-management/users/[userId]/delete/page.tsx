'use client'

import { use } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'

import { GovukHeading, GovukButton } from '@/components/govuk'
import {
  getTargetUserUsersUserIdGetOptions,
  deleteUserUsersUserIdDeleteMutation,
} from '@/lib/client/@tanstack/react-query.gen'

export default function UserPage(props: {
  params: Promise<{ userId: string }>
}) {
  const router = useRouter()

  const { userId } = use(props.params)
  const userResponse = useQuery({
    ...getTargetUserUsersUserIdGetOptions({
      path: {
        user_id: userId,
      },
    }),
  })

  const { mutate: deleteUser } = useMutation({
    ...deleteUserUsersUserIdDeleteMutation(),
    onSuccess() {
      router.replace('/user-management')
    },
  })

  return (
    <>
      <GovukHeading>
        Delete user account: {userResponse.data?.name}
      </GovukHeading>

      <GovukButton
        variant="warning"
        onClick={() => deleteUser({ path: { user_id: userId } })}
      >
        Delete account
      </GovukButton>
    </>
  )
}
