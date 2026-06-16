'use client'

import { use } from 'react'
import { useQuery } from '@tanstack/react-query'

import { GovukHeading } from '@/components/govuk/heading'
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
      <p>{userId}</p>
      {JSON.stringify(userResponse.data, null, 2)}
    </>
  )
}
