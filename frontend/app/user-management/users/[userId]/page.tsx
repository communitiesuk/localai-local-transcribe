'use client'

import { use, useCallback, useEffect } from 'react'
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
  getUserUsersMeGetQueryKey,
  updateUserRolesUsersUserIdRolesPatchMutation,
} from '@/lib/client/@tanstack/react-query.gen'
import { useRouter } from 'next/navigation'
import { Loader2 } from 'lucide-react'
import { GetUserResponse, UserRole } from '@/lib/client'
import { Controller, useForm } from 'react-hook-form'

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

      {targetUser && <RolesForm user={targetUser} />}

      <GovukButtonLink
        variant="warning"
        href={`/user-management/users/${userId}/delete`}
      >
        Delete account
      </GovukButtonLink>

      <hr className="govuk-section-break govuk-section-break--visible govuk-section-break--l" />

      <GovukDetails summary="Breakdown of role-based permissions">
        <GovukList spaced>
          <GovukListItem>
            <strong>Standard user:</strong> can create and manage their own
            meetings and meeting summaries.
          </GovukListItem>
          <GovukListItem>
            <strong>Admin:</strong> can invite standard users, toggle standard &
            admin status of accounts and can delete users within their
            organisation.
          </GovukListItem>
        </GovukList>
      </GovukDetails>
    </>
  )
}

type UserRoleForm = { role: UserRole }

function RolesForm({ user }: { user: GetUserResponse }) {
  const form = useForm<UserRoleForm>({
    defaultValues: {
      role: user.roles ? (user.roles[0] as UserRole) : undefined,
    },
  })
  const queryClient = useQueryClient()
  const { mutateAsync, isPending } = useMutation({
    ...updateUserRolesUsersUserIdRolesPatchMutation(),
  })

  const onSubmit = useCallback(
    async (data: UserRoleForm) => {
      await mutateAsync(
        {
          body: {
            roles: data.role === undefined ? [] : [data.role],
          },
          path: {
            user_id: user.id,
          },
        },
        {
          onSuccess() {
            queryClient.invalidateQueries({
              queryKey: getUserUsersMeGetQueryKey(),
            })
          },
        }
      )
    },
    [user.id, mutateAsync, queryClient]
  )

  return (
    <form
      onSubmit={form.handleSubmit(onSubmit)}
      className="govuk-!-margin-top-6"
    >
      <GovukFormGroup>
        <GovukFieldset aria-describedby="role-hint">
          <GovukLegend size="m">Role</GovukLegend>
          <GovukHint id="role-hint">
            Different roles come with varying access to Local Transcribe's
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
                  { label: 'Admin', value: 'mhclg_support_admin' },
                ]}
              />
            )}
          />
        </GovukFieldset>
      </GovukFormGroup>

      <div className="govuk-!-margin-top-6">
        <GovukButton type="submit" disabled={isPending}>
          {isPending ? (
            <span className="flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              Saving...
            </span>
          ) : (
            'Save changes'
          )}
        </GovukButton>
      </div>
    </form>
  )
}
