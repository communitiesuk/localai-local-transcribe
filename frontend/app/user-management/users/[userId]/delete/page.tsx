'use client'

import { use, useEffect } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'

import {
  GovukHeading,
  GovukButton,
  GovukWarningText,
  GovukBackLink,
} from '@/components/govuk'
import {
  getTargetUserUsersUserIdGetOptions,
  deleteUserUsersUserIdDeleteMutation,
} from '@/lib/client/@tanstack/react-query.gen'
import { useAuthorisedOrgUser } from '@/hooks/use-authorised-user'
import { Loader2 } from 'lucide-react'

export default function UserPageDelete(props: {
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
    user: currentUser,
    isError: authError,
  } = useAuthorisedOrgUser(targetUser?.organisation_id ?? undefined)

  const authReady = !targetUserLoading && !authLoading
  const pageError = targetUserError || authError

  useEffect(() => {
    if (pageError) {
      router.replace('/generic-error')
    }

    if (!pageError && authReady && !isAllowed) {
      router.replace('/unauthorised')
    }
  }, [pageError, authReady, isAllowed, router])

  let redirectPath =
    currentUser?.id === targetUser?.id ? '/' : '/user-management' // go to hompage if user deletes themself

  const { mutate: deleteUser } = useMutation({
    ...deleteUserUsersUserIdDeleteMutation(),
    onSuccess() {
      router.replace(redirectPath)
    },
  })

  if (targetUserLoading || authLoading) {
    return <Loader2 className="animate-spin" />
  }

  if (pageError) return null

  return (
    <>
      <GovukBackLink />
      <GovukHeading>Delete user account: {targetUser?.name}</GovukHeading>

      <p className="govuk-body">
        Are you sure you want to delete the user account for{' '}
        <strong>
          {targetUser?.name} ({targetUser?.email})
        </strong>
        ?
      </p>

      <p className="govuk-body">
        Make sure you are removing the correct user before you continue.
      </p>

      <p className="govuk-body">
        By proceeding, they will be sent a notification of deletion to the email
        address above. You will also need to invite this user again to give them
        access.
      </p>

      <GovukWarningText>
        Once deleted, you will not be able to recover this user account and its
        associate recordings
      </GovukWarningText>

      <div className="flex items-baseline gap-x-5">
        <GovukButton
          variant="warning"
          onClick={() => deleteUser({ path: { user_id: userId } })}
        >
          Delete account
        </GovukButton>

        <a className="govuk-link" href={`/user-management/users/${userId}`}>
          Cancel
        </a>
      </div>
    </>
  )
}
