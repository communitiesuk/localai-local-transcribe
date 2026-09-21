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
import {
  GovukFormGroup,
  GovukHint,
  GovukInput,
  GovukLabel,
} from '@/components/govuk'

export default function AdminAddUserPage() {
  const router = useRouter()
  const invalidDomainError =
    'Please enter an email address with a valid domain for your organisation.'
  const existingEmailError = 'This email is already registered with an account'

  const {
    name: storedName,
    email: storedEmail,
    evaluationId: storedEvaluationId,
    organisationId,
    setInviteDetails,
    clearInviteDetails,
  } = useInviteUserStore()
  const [name, setName] = useState(storedName)
  const [email, setEmail] = useState(storedEmail)
  const [evaluationId, setEvaluationId] = useState(storedEvaluationId)
  const [hasError, setHasError] = useState(false)
  const [errorMessage, setErrorMessage] = useState(invalidDomainError)
  const [nameError, setNameError] = useState<string | null>(null)
  const [evaluationIdError, setEvaluationIdError] = useState<string | null>(
    null
  )

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
    setNameError(null)
    setEvaluationIdError(null)
    setHasError(false)

    if (!currentUser?.organisation_id) {
      return
    }

    if (!name.trim()) {
      setNameError('Enter a name')
      return
    }

    if (!email.trim()) {
      setErrorMessage('Enter an email address')
      setHasError(true)
      return
    }

    if (!evaluationId.trim()) {
      setEvaluationIdError('Enter an evaluation ID')
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

    setInviteDetails(name, email, evaluationId.trim(), organisationId)
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
      <form onSubmit={handleSubmit} noValidate>
        <fieldset className="govuk-fieldset">
          <legend className="govuk-fieldset__legend govuk-fieldset__legend--l">
            <h1 className="govuk-fieldset__heading">Invite new user</h1>
          </legend>

          <div
            className={cn(
              'govuk-form-group',
              nameError && 'govuk-form-group--error'
            )}
          >
            <label className="govuk-label" htmlFor="invitee-name">
              Name
            </label>
            {nameError && (
              <p id="invitee-name-error" className="govuk-error-message">
                <span className="govuk-visually-hidden">Error:</span>
                {nameError}
              </p>
            )}
            <input
              className={cn(
                'govuk-input govuk-input--width-30',
                nameError && 'govuk-input--error'
              )}
              id="invitee-name"
              name="name"
              type="text"
              spellCheck="false"
              value={name}
              onChange={(e) => setName(e.target.value)}
              aria-invalid={nameError ? true : undefined}
              aria-describedby={nameError ? 'invitee-name-error' : undefined}
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
              aria-invalid={hasError ? true : undefined}
              aria-describedby={
                hasError ? 'invitee-email-address-error' : undefined
              }
            />
          </div>

          <GovukFormGroup hasError={!!evaluationIdError}>
            <GovukLabel htmlFor="invitee-evaluation-id">
              Evaluation ID
            </GovukLabel>
            <GovukHint id="invitee-evaluation-id-hint">
              Use the evaluation ID that MHCLG provided for this person. It
              cannot be one that is already in use, and you will not be able to
              see it in Local Transcribe again.
            </GovukHint>
            {evaluationIdError && (
              <p
                id="invitee-evaluation-id-error"
                className="govuk-error-message"
              >
                <span className="govuk-visually-hidden">Error:</span>
                {evaluationIdError}
              </p>
            )}
            <GovukInput
              id="invitee-evaluation-id"
              name="evaluationId"
              type="text"
              spellCheck="false"
              className="govuk-input--width-20"
              value={evaluationId}
              onChange={(e) => setEvaluationId(e.target.value)}
              aria-invalid={evaluationIdError ? true : undefined}
              aria-describedby={
                evaluationIdError
                  ? 'invitee-evaluation-id-hint invitee-evaluation-id-error'
                  : 'invitee-evaluation-id-hint'
              }
            />
          </GovukFormGroup>

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
