'use client'
import { useRouter } from 'next/navigation'
import { useState } from 'react'
import { cn } from '@/lib/utils'
import { useAuthorisedUser } from '@/hooks/use-authorised-user'
import { useOrganisation } from '@/hooks/use-organisation'
import { UserRole } from '@/lib/utils'
import isAllowedDomain from '@/utils/allowed-domains'
import { Loader2 } from 'lucide-react'

export default function AdminAddUserPage() {
  const router = useRouter()

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

  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [hasError, setHasError] = useState(false)

  const handleSubmit = (e: React.SyntheticEvent<HTMLFormElement>) => {
    e.preventDefault()

    if (!isAllowedDomain(email, organisation?.allowed_domains ?? [])) {
      console.error('Email domain is not allowed for this organisation.', email)
      setHasError(true)
      return
    }
    /*
        TODO: Validate if email exists
        This should ideally be handled in the backend during creation
        Created AIILG-668 to cover this work, but for now, allowing the user 
        to proceed to the confirmation page where the actual creation happens.
        An error message should be displayed if the email is invalid or already exists
        For now, solely checking if the email is lies within the accepted domains 
        list and displaying the set error message if not
        */

    router.push(
      `/invite-user/confirm?name=${encodeURIComponent(name)}&email=${encodeURIComponent(email)}`
    )
  }

  const handleCancel = (e: React.SyntheticEvent<HTMLAnchorElement>) => {
    e.preventDefault()
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
                Please enter an email address with a valid domain for your
                organisation.
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
