'use client'

import Link from 'next/link'
import { Controller, useForm } from 'react-hook-form'
import {
  GovukButton,
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
}: {
  defaultValues: string[]
  onSubmit: (data: EditDomainsFormData) => void
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

      <div className="govuk-button-group">
        <GovukButton type="submit">Save</GovukButton>
        <Link href="/user-management" className="govuk-link">
          Cancel
        </Link>
      </div>
    </form>
  )
}
