'use client'

import {
  GovukBackLink,
  GovukButton,
  GovukButtonGroup,
  GovukDetails,
  GovukErrorSummary,
  GovukFormGroup,
  GovukHint,
  GovukLabel,
  GovukTextarea,
} from '@/components/govuk'
import { useAuthorisedUser } from '@/hooks/use-authorised-user'
import { useOrganisation } from '@/hooks/use-organisation'
import { OrganisationResponse } from '@/lib/client'
import { useInviteUserStore } from '@/stores/use-invite-user-store'
import {
  getOrganisationOrganisationsOrganisationIdGetQueryKey,
  updateOrganisationOrganisationsOrganisationIdPatchMutation,
} from '@/lib/client/@tanstack/react-query.gen'
import { UserRole } from '@/lib/utils'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Loader2 } from 'lucide-react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useCallback } from 'react'
import { Controller, useForm } from 'react-hook-form'
import { toast } from 'sonner'

function parseDomains(value: string): string[] {
  return value
    .split('\n')
    .map((domain) => domain.trim())
    .filter(Boolean)
}

type EditDomainsForm = { domains: string }

export default function EditApprovedDomainsPage() {
  const { currentUser, isLoading: userLoading } = useAuthorisedUser([
    UserRole.MHCLG_SUPPORT_ADMIN,
  ])

  const { organisationId: selectedOrganisationId } = useInviteUserStore()

  const { data: organisation, isLoading: organisationLoading } =
    useOrganisation(
      selectedOrganisationId || currentUser?.organisation_id || ''
    )

  if (userLoading || organisationLoading || !organisation) {
    return (
      <div className="govuk-body flex items-center gap-2">
        <Loader2 className="animate-spin" />
        Loading...
      </div>
    )
  }

  return (
    <>
      <GovukBackLink />
      <h1 className="govuk-heading-l">Edit approved domains</h1>
      <h2 className="govuk-heading-s govuk-!-margin-bottom-2">
        {organisation.name}
      </h2>
      <EditDomainsForm organisation={organisation} />
    </>
  )
}

function EditDomainsForm({
  organisation,
}: {
  organisation: OrganisationResponse
}) {
  const router = useRouter()
  const queryClient = useQueryClient()

  const form = useForm<EditDomainsForm>({
    defaultValues: {
      domains: organisation.allowed_domains.join('\n'),
    },
  })

  const { mutateAsync, isPending } = useMutation({
    ...updateOrganisationOrganisationsOrganisationIdPatchMutation(),
  })

  const onSubmit = useCallback(
    async (data: EditDomainsForm) => {
      await mutateAsync(
        {
          path: { organisation_id: organisation.id },
          body: { allowed_domains: parseDomains(data.domains) },
        },
        {
          onSuccess(updatedOrganisation) {
            queryClient.setQueryData(
              getOrganisationOrganisationsOrganisationIdGetQueryKey({
                path: { organisation_id: organisation.id },
              }),
              updatedOrganisation
            )
            toast.success('Approved domains updated')
            router.push('/user-management')
          },
          onError() {
            toast.error('Failed to update approved domains')
          },
        }
      )
    },
    [mutateAsync, organisation.id, queryClient, router]
  )

  const domainsError = form.formState.errors.domains

  return (
    <form onSubmit={form.handleSubmit(onSubmit)}>
      {domainsError && (
        <GovukErrorSummary
          errorList={[{ href: '#domains', text: domainsError.message ?? '' }]}
        />
      )}

      <GovukFormGroup hasError={!!domainsError}>
        <GovukLabel htmlFor="domains">Approved domains</GovukLabel>
        <GovukHint id="domains-hint">
          Please list any approved domains on individual lines and without the
          &apos;@&apos; symbol (e.g. &apos;communities.gov.uk&apos;).
        </GovukHint>
        {domainsError && (
          <p id="domains-error" className="govuk-error-message">
            <span className="govuk-visually-hidden">Error:</span>{' '}
            {domainsError.message}
          </p>
        )}
        <Controller
          control={form.control}
          name="domains"
          rules={{
            validate: (value) =>
              parseDomains(value).length > 0 ||
              'Enter at least one approved domain',
          }}
          render={({ field: { value, onChange, ref, disabled } }) => (
            <GovukTextarea
              id="domains"
              name="domains"
              rows={8}
              aria-describedby={
                domainsError ? 'domains-error domains-hint' : 'domains-hint'
              }
              value={value}
              onChange={onChange}
              disabled={disabled}
              ref={ref}
            />
          )}
        />
      </GovukFormGroup>

      <GovukButtonGroup>
        <GovukButton type="submit" disabled={isPending}>
          Save
        </GovukButton>
        <Link href="/user-management" className="govuk-link">
          Cancel
        </Link>
      </GovukButtonGroup>

      <hr className="govuk-section-break govuk-section-break--visible govuk-section-break--l" />

      <GovukDetails summary="More about approved domains">
        <p className="govuk-body">
          These are the email address domains that are able to be invited to a
          given organisation using Internal Access authentication.
        </p>
        <p className="govuk-body">
          Email addresses without an associated approved domain will not be able
          to be invited.
        </p>
      </GovukDetails>
    </form>
  )
}
