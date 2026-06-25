'use client'

import {
  GovukButton,
  GovukDetails,
  GovukErrorSummary,
  GovukFormGroup,
  GovukHint,
  GovukLabel,
  GovukTextarea,
} from '@/components/govuk'
import { OrganisationResponse } from '@/lib/client'
import {
  getOrganisationOrganisationsOrganisationIdGetQueryKey,
  updateOrganisationOrganisationsOrganisationIdPatchMutation,
} from '@/lib/client/@tanstack/react-query.gen'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useCallback } from 'react'
import { Controller, useForm } from 'react-hook-form'
import { toast } from 'sonner'

type EditDomainsFormData = { domains: string }

function parseDomains(value: string): string[] {
  return value
    .split('\n')
    .map((domain) => domain.trim())
    .filter(Boolean)
}

export function EditDomainsForm({
  organisation,
}: {
  organisation: OrganisationResponse
}) {
  const router = useRouter()
  const queryClient = useQueryClient()

  const form = useForm<EditDomainsFormData>({
    defaultValues: {
      domains: organisation.allowed_domains.join('\n'),
    },
  })

  const { mutateAsync, isPending } = useMutation({
    ...updateOrganisationOrganisationsOrganisationIdPatchMutation(),
  })

  const onSubmit = useCallback(
    async (data: EditDomainsFormData) => {
      await mutateAsync(
        {
          path: { organisation_id: organisation.id },
          body: { allowed_domains: parseDomains(data.domains) },
        },
        {
          onSuccess() {
            queryClient.invalidateQueries({
              queryKey: getOrganisationOrganisationsOrganisationIdGetQueryKey({
                path: { organisation_id: organisation.id },
              }),
            })
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

      <div className="govuk-button-group">
        <GovukButton type="submit" disabled={isPending}>
          Save
        </GovukButton>
        <Link href="/user-management" className="govuk-link">
          Cancel
        </Link>
      </div>

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
