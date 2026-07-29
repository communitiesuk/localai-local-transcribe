'use client'

import { useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthorisedUser } from '@/hooks/use-authorised-user'
import { hasAnyRole, UserRole } from '@/lib/utils'
import { useInviteUserStore } from '@/stores/use-invite-user-store'
import { useOrganisation } from '@/hooks/use-organisation'
import { createUserUsersPostMutation } from '@/lib/client/@tanstack/react-query.gen'
import { Loader2 } from 'lucide-react'
import { useMutation } from '@tanstack/react-query'

export default function AdminAddUserConfirmPage() {
  const router = useRouter()
  const { name, email, organisationId, clearInviteDetails } =
    useInviteUserStore()
  const submitInProgress = useRef(false)

  const {
    currentUser,
    isLoading: userLoading,
    isError: userError,
  } = useAuthorisedUser([
    UserRole.LOCAL_AUTHORITY_ADMIN,
    UserRole.MHCLG_SUPPORT_ADMIN,
  ])

  const { data: organisation } = useOrganisation(
    currentUser?.organisation_id ?? ''
  )

  const createUserMutation = useMutation(createUserUsersPostMutation())

  useEffect(() => {
    if (submitInProgress.current) return
    if (!name || !email) {
      router.replace('/invite-user')
    }
  }, [name, email, router])

  if (!name || !email || !organisation?.id) {
    return <Loader2 className="animate-spin" />
  }

  const is_Support_Admin = hasAnyRole(currentUser?.roles, [
    UserRole.MHCLG_SUPPORT_ADMIN,
  ])
  const is_LA_Admin = hasAnyRole(currentUser?.roles, [
    UserRole.LOCAL_AUTHORITY_ADMIN,
  ])

  const handleCreateUser = async () => {
    submitInProgress.current = true
    if (!is_Support_Admin && !is_LA_Admin) return

    if (!name || !email) {
      console.error('Missing required fields for user creation:', {
        name,
        email,
      })
      submitInProgress.current = false
      return
    }

    if (is_Support_Admin) {
      console.log('Creating user as Support Admin:', {
        name,
        email,
        organisationId,
      })

      try {
        if (!organisationId) {
          console.error(
            'Organisation ID is missing for Support Admin user creation.'
          )
          submitInProgress.current = false
          return
        }

        console.log('Creating user with organisation ID:', organisationId)

        await createUserMutation.mutateAsync({
          body: {
            name: name,
            email: email,
            organisation_id: organisationId,
          },
        })
        router.push('/user-management')
        clearInviteDetails()
      } catch (error) {
        submitInProgress.current = false
        console.error('Failed to create user:', error)
        // Awaiting error logic from UCD
      }
    }

    if (is_LA_Admin) {
      try {
        await createUserMutation.mutateAsync({
          body: {
            name: name,
            email: email,
            organisation_id: organisation?.id,
          },
        })
        router.push('/user-management')
        clearInviteDetails()
      } catch (error) {
        submitInProgress.current = false
        console.error('Failed to create user:', error)
        // Awaiting error logic from UCD
      }
    }
  }
  return (
    <>
      {userLoading && <Loader2 className="animate-spin" />}

      {userError && <p>Error: Failed to load users.</p>}

      <div>
        <h1 className="govuk-heading-l">Invite new user</h1>
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-three-quarters">
            <p className="govuk-body govuk-!-margin-bottom-5">
              {' '}
              Are you sure you want to invite {name} ({email}) to use Local
              Transcribe as a part of your organisation?
            </p>

            <p className="govuk-body govuk-!-margin-bottom-5">
              By proceeding this person will be sent an invitation link to the
              email address stated above. They will appear as ‘Pending’ in your
              system until they complete their onboarding process.
            </p>

            <p className="govuk-body govuk-!-margin-bottom-5">
              They will be granted standard user access by default. If you would
              like to grant them organisation admin permissions you can change this in their
              user account.
            </p>

            <div className="govuk-warning-text">
              <span className="govuk-warning-text__icon" aria-hidden="true">
                !
              </span>
              <strong className="govuk-warning-text__text">
                <span className="govuk-visually-hidden">Warning</span>
                Make sure you are inviting the correct person before you
                continue
              </strong>
            </div>
          </div>
        </div>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '1rem',
          }}
          className="govuk-button-group"
        >
          <button
            type="submit"
            className="govuk-button"
            data-module="govuk-button"
            data-prevent-double-click="true"
            onClick={handleCreateUser}
          >
            Invite
          </button>

          <a href="/invite-user/" className="govuk-link">
            Cancel
          </a>
        </div>
      </div>
    </>
  )
}
