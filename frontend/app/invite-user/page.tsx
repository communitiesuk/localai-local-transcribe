'use client'
import { useRouter } from 'next/navigation'
import { useState } from 'react'
import { cn } from '@/lib/utils'
import { useAuthorisedUser } from '@/hooks/use-authorised-user'
import { useInviteUserStore } from '@/stores/use-invite-user-store'
import { useOrganisation } from '@/hooks/use-organisation'
import { UserRole } from '@/lib/utils'
import isAllowedDomain from '@/utils/allowed-domains'
import { Loader2 } from 'lucide-react'
import { userExistsUsersUserExistsGet } from '@/lib/client'

export default function AdminAddUserPage() {
  const router = useRouter()
  const invalidDomainError =
    'Please enter an email address with a valid domain for your organisation.'
  const existingEmailError = 'This email is already registered with an account'

  const {
    name: storedName,
    email: storedEmail,
    organisationId,
    setInviteDetails,
    clearInviteDetails,
  } = useInviteUserStore()
  const [name, setName] = useState(storedName)
  const [email, setEmail] = useState(storedEmail)
  const [hasError, setHasError] = useState(false)
  const [errorMessage, setErrorMessage] = useState(invalidDomainError)

  const {
    currentUser,
    isLoading: userLoading,
    isError: userError,
  } = useAuthorisedUser([
    UserRole.LOCAL_AUTHORITY_ADMIN,
    UserRole.MHCLG_SUPPORT_ADMIN,
  ])

  const { data: organisation } = useOrganisation(
    organisationId || currentUser?.organisation_id || ''
  )

  const handleSubmit = async (e: React.SyntheticEvent<HTMLFormElement>) => {
    e.preventDefault()

    if (!currentUser?.organisation_id) {
      return
    }

    if (!isAllowedDomain(email, organisation?.allowed_domains ?? [])) {
      console.error(invalidDomainError, email)
      setErrorMessage(invalidDomainError)
      setHasError(true)
      return
    }

    const response = await userExistsUsersUserExistsGet({
      query: {
        email,
        organisation_id: currentUser.organisation_id,
      },
    })

    if (response.data?.exists) {
      setErrorMessage(existingEmailError)
      setHasError(true)
      return
    }

    setInviteDetails(name, email, organisationId)
    router.push('/invite-user/confirm')
  }

  const handleCancel = (e: React.SyntheticEvent<HTMLAnchorElement>) => {
    e.preventDefault()
    clearInviteDetails()
    setErrorMessage('')
    setHasError(false)
  }

  if (userLoading) return <Loader2 className="animate-spin" />

  if (userError) return <p>Error: Failed to load users.</p>

  return (
    <div>
      <form onSubmit={handleSubmit}>
        <fieldset className="govuk-fieldset">
          <legend className="govuk-fieldset__legend govuk-fieldset__legend--l">
            <h1 className="govuk-fieldset__heading">Invite new user</h1>
          </legend>

          <div className="govuk-form-group">
            <label className="govuk-label" htmlFor="invitee-name">
              Name
            </label>
            <input
              className="govuk-input govuk-input--width-30"
              id="invitee-name"
              name="name"
              type="text"
              spellCheck="false"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </div>

          <div
            className={cn(
              'govuk-form-group',
              hasError && 'govuk-form-group--error'
            )}
          >
            <label className="govuk-label" htmlFor="invitee-email-address">
              Email address
            </label>

            {hasError && (
              <p
                id="invitee-email-address-error"
                className="govuk-error-message"
              >
                <span className="govuk-visually-hidden">Error:</span>
                {errorMessage}
              </p>
            )}

            <input
              className={cn(
                'govuk-input govuk-input--width-30',
                hasError && 'govuk-input--error'
              )}
              id="invitee-email-address"
              name="emailAddress"
              type="email"
              spellCheck="false"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              aria-describedby={
                hasError ? 'invitee-email-address-error' : undefined
              }
              required
            />
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
            >
              Continue
            </button>

            <a
              href="/admin/users"
              className="govuk-link"
              onClick={handleCancel}
            >
              Cancel
            </a>
          </div>
        </fieldset>
      </form>
      <details className="govuk-details">
        <summary className="govuk-details__summary">
          <span className="govuk-details__summary-text">
            Accepted email domains for your organisation
          </span>
        </summary>
        <div className="govuk-details__text">
          <ul className="govuk-list govuk-list--bullet">
            {organisation?.allowed_domains.map((domain) => (
              <li key={domain}>{domain}</li>
            ))}
          </ul>
        </div>
      </details>
    </div>
  )
}
