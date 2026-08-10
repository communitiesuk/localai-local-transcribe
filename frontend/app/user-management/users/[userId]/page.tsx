'use client'

import { use, useCallback, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
  GovukHeading,
  GovukButtonLink,
  GovukBackLink,
  GovukFormGroup,
  GovukFieldset,
  GovukLegend,
  GovukHint,
  GovukRadios,
  GovukButton,
  GovukDetails,
  GovukList,
  GovukListItem,
  GovukButtonGroup,
  GovukNotificationBanner,
} from '@/components/govuk'
import {
  GovukTable,
  GovukTableBody,
  GovukTableRow,
  GovukTableCell,
  GovukTableHeaderCell,
} from '@/components/govuk/table'
import {
  getTargetUserUsersUserIdGetOptions,
  getTargetUserUsersUserIdGetQueryKey,
  updateUserRolesUsersUserIdRolesPatchMutation,
} from '@/lib/client/@tanstack/react-query.gen'
import { useRouter } from 'next/navigation'
import { Loader2 } from 'lucide-react'
import { GetUserResponse, UserRole } from '@/lib/client'
import { Controller, useForm } from 'react-hook-form'
import { useBannerStore } from '@/stores/use-banner-store'
import { formatCurrentDateTime } from '@/lib/utils'

export default function UserPage(props: {
  params: Promise<{ userId: string }>
}) {
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

  if (targetUserLoading) {
    return <Loader2 className="animate-spin" />
  }

  // Surface the failure to the nearest error boundary (app/error.tsx),
  // which renders the canonical GOV.UK "there is a problem" page.
  if (targetUserError) {
    throw new Error('Unable to load user')
  }

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

      {targetUser && <RolesForm user={targetUser} />}

      <hr className="govuk-section-break govuk-section-break--visible govuk-section-break--l" />

      <GovukDetails summary="Breakdown of role-based permissions">
        <GovukList spaced type="bullet">
          <GovukListItem>
            <strong>Standard user:</strong> can create and manage their own
            meetings and meeting summaries.
          </GovukListItem>
          <GovukListItem>
            <strong>Organisation admin:</strong> can invite standard users,
            toggle standard & organisation admin status of accounts and can
            delete users within their organisation.
          </GovukListItem>
        </GovukList>
      </GovukDetails>
    </>
  )
}

type UserRoleForm = { role: AssignableUserRole | undefined }
type AssignableUserRole = Extract<
  UserRole,
  'standard_user' | 'local_authority_admin'
>

const ASSIGNABLE_USER_ROLES: readonly AssignableUserRole[] = [
  'standard_user',
  'local_authority_admin',
]

function getDefaultAssignableRole(
  userRoles: UserRole[] | undefined
): AssignableUserRole | undefined {
  if (!userRoles?.length) {
    return undefined
  }

  if (userRoles.includes('local_authority_admin')) {
    return 'local_authority_admin'
  }

  if (userRoles.includes('standard_user')) {
    return 'standard_user'
  }

  return undefined
}

function getRoleUpdateErrorMessage(error: unknown): string {
  if (
    typeof error === 'object' &&
    error !== null &&
    'error' in error &&
    typeof error.error === 'object' &&
    error.error !== null &&
    'detail' in error.error &&
    typeof error.error.detail === 'string'
  ) {
    return error.error.detail
  }

  return 'Could not update user permissions. Please try again.'
}

function RolesForm({ user }: { user: GetUserResponse }) {
  const router = useRouter()
  const setBanner = useBannerStore((store) => store.setBanner)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const defaultRole = getDefaultAssignableRole(user.roles)

  const form = useForm<UserRoleForm>({
    defaultValues: {
      role: defaultRole,
    },
  })
  const queryClient = useQueryClient()
  const { mutateAsync, isPending } = useMutation({
    ...updateUserRolesUsersUserIdRolesPatchMutation(),
  })

  const onSubmit = useCallback(
    async (data: UserRoleForm) => {
      if (!data.role || !ASSIGNABLE_USER_ROLES.includes(data.role)) {
        return
      }

      setSubmitError(null)

      try {
        await mutateAsync({
          body: {
            roles: [data.role],
          },
          path: {
            user_id: user.id,
          },
        })
      } catch (error) {
        setSubmitError(getRoleUpdateErrorMessage(error))
        return
      }

      queryClient.invalidateQueries({
        queryKey: getTargetUserUsersUserIdGetQueryKey({
          path: { user_id: user.id },
        }),
      })
      setBanner({
        variant: 'success',
        title: 'Success',
        message: `Permissions for ${user.name ?? user.email} saved at ${formatCurrentDateTime()}`,
      })
      router.replace('/user-management')
    },
    [
      user.id,
      user.name,
      user.email,
      setBanner,
      mutateAsync,
      queryClient,
      router,
    ]
  )

  return (
    <form
      onSubmit={form.handleSubmit(onSubmit)}
      className="govuk-!-margin-top-6"
    >
      {submitError && (
        <GovukNotificationBanner title="There is a problem" variant="important">
          {submitError}
        </GovukNotificationBanner>
      )}

      <GovukFormGroup>
        <GovukFieldset aria-describedby="role-hint">
          <GovukLegend size="m">Role</GovukLegend>
          <GovukHint id="role-hint">
            Different roles come with varying access to Local Transcribe&apos;s
            features
          </GovukHint>
          <Controller
            control={form.control}
            name="role"
            render={({ field: { onChange, value, ref, disabled } }) => (
              <GovukRadios
                name="role"
                value={value}
                onChange={onChange}
                disabled={disabled}
                ref={ref}
                options={[
                  { label: 'Standard user', value: 'standard_user' },
                  {
                    label: 'Organisation admin',
                    value: 'local_authority_admin',
                  },
                ]}
              />
            )}
          />
        </GovukFieldset>
      </GovukFormGroup>

      <GovukButtonGroup className="govuk-!-margin-top-6">
        <GovukButton type="submit" disabled={isPending}>
          Save changes
        </GovukButton>
        <GovukButtonLink
          variant="warning"
          href={`/user-management/users/${user.id}/delete`}
        >
          Delete account
        </GovukButtonLink>
      </GovukButtonGroup>
    </form>
  )
}
