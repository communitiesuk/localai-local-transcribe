'use client'

import Link from 'next/link'
import { Controller, useForm } from 'react-hook-form'
import {
  GovukButton,
  GovukButtonGroup,
  GovukDetails,
  GovukErrorSummary,
  GovukFormGroup,
  GovukHint,
  GovukLabel,
  GovukTextarea,
} from '@/components/govuk'
import { parseDomains } from '@/lib/utils'

export type EditDomainsFormData = { domains: string }

export function EditDomainsForm({
  defaultValues,
  onSubmit,
  isPending = false,
  buttonText = 'Save',
  buttonPendingText = 'Saving',
  cancelHref = '/user-management',
}: {
  defaultValues: string[]
  onSubmit: (data: EditDomainsFormData) => void
  isPending?: boolean
  buttonText?: string
  buttonPendingText?: string
  cancelHref?: string
}) {
  const form = useForm<EditDomainsFormData>({
    defaultValues: {
      domains: defaultValues.join('\n'),
    },
  })

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
          {isPending ? buttonPendingText : buttonText}
        </GovukButton>
        <Link href={cancelHref} className="govuk-link">
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
