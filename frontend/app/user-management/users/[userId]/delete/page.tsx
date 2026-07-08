'use client'

import { use, useEffect } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'

import { Loader2 } from 'lucide-react'
import {
  GovukHeading,
  GovukButton,
  GovukWarningText,
  GovukBackLink,
} from '@/components/govuk'
import {
  getUserUsersMeGetOptions,
  getTargetUserUsersUserIdGetOptions,
  deleteUserUsersUserIdDeleteMutation,
} from '@/lib/client/@tanstack/react-query.gen'
import { useBannerStore } from '@/stores/use-banner-store'
import { formatCurrentDateTime } from '@/lib/utils'

export default function UserPageDelete(props: {
  params: Promise<{ userId: string }>
}) {
  const router = useRouter()
  const setBanner = useBannerStore((store) => store.setBanner)

  const { userId } = use(props.params)

  const { data: currentUser } = useQuery({ ...getUserUsersMeGetOptions() })

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

  const redirectPath =
    currentUser?.id === targetUser?.id ? '/' : '/user-management' // go to hompage if user deletes themself

  const { mutate: deleteUser, isPending: deletePending } = useMutation({
    ...deleteUserUsersUserIdDeleteMutation(),
    onSuccess() {
      setBanner({
        variant: 'success',
        title: 'Success',
        message: `${targetUser?.name} was successfully deleted at ${formatCurrentDateTime()}`,
      })
      router.replace(redirectPath)
    },
  })

  if (targetUserLoading) {
    return <Loader2 className="animate-spin" />
  }

  if (targetUserError) return null

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
          {deletePending ? 'Deleting account...' : 'Delete account'}
        </GovukButton>

        <a className="govuk-link" href={`/user-management/users/${userId}`}>
          Cancel
        </a>
      </div>
    </>
  )
}
