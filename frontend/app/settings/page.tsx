'use client'

import { useEffect, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useForm, useWatch } from 'react-hook-form'
import { Loader2 } from 'lucide-react'
import {
  GovukBackLink,
  GovukBody,
  GovukButton,
  GovukErrorSummary,
  GovukFieldset,
  GovukFormGroup,
  GovukHeading,
  GovukHint,
  GovukInput,
  GovukLabel,
  GovukLegend,
  GovukNotificationBanner,
  GovukRadios,
  GovukSectionBreak,
  GovukTable,
  GovukTableBody,
  GovukTableCell,
  GovukTableHeaderCell,
  GovukTableRow,
} from '@/components/govuk'
import type { GetUserResponse, UserRole } from '@/lib/client'
import {
  getUserUsersMeGetOptions,
  getUserUsersMeGetQueryKey,
  updateDataRetentionUsersDataRetentionPatchMutation,
} from '@/lib/client/@tanstack/react-query.gen'
import { MicrophoneSettings } from '@/components/settings/microphone-settings'
import { validateCustomRetention } from '@/lib/data-retention'

type RetentionForm = {
  period: string
  customDays: string
}

const roleLabels: Record<UserRole, string> = {
  standard_user: 'Standard',
  local_authority_admin: 'Organisation admin',
  mhclg_support_admin: 'MHCLG support admin',
}

function retentionValues(days: number): RetentionForm {
  const preset = [7, 14, 30].includes(days)
  return {
    period: preset ? String(days) : 'custom',
    customDays: preset ? '' : String(days),
  }
}

export default function SettingsPage() {
  const { data: user, isError } = useQuery(getUserUsersMeGetOptions())
  if (isError) throw new Error('Unable to load settings')
  if (!user) {
    return (
      <GovukBody className="flex items-center gap-2" role="status">
        <Loader2 className="animate-spin" aria-hidden="true" />
        Loading...
      </GovukBody>
    )
  }
  return <SettingsContent key={user.id} user={user} />
}

function SettingsContent({ user }: { user: GetUserResponse }) {
  const form = useForm<RetentionForm>({
    defaultValues: retentionValues(user.data_retention_days),
  })
  const [savedDays, setSavedDays] = useState(user.data_retention_days)
  const [success, setSuccess] = useState<string | null>(null)
  const [saveError, setSaveError] = useState<string | null>(null)
  const queryClient = useQueryClient()
  const { mutateAsync, isPending } = useMutation(
    updateDataRetentionUsersDataRetentionPatchMutation()
  )
  const [period, customDays] = useWatch({
    control: form.control,
    name: ['period', 'customDays'],
  })
  const validationError =
    period === 'custom' ? validateCustomRetention(customDays) : null
  const days = Number(period === 'custom' ? customDays.trim() : period)
  const error = validationError ?? saveError
  const errorRef = useRef<HTMLDivElement>(null)
  const successRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (success) successRef.current?.focus()
    else if (saveError) errorRef.current?.focus()
  }, [saveError, success])

  function clearFeedback() {
    setSaveError(null)
    setSuccess(null)
  }

  async function saveRetention() {
    if (isPending || validationError || days === savedDays) return
    clearFeedback()
    let updatedUser: GetUserResponse
    try {
      updatedUser = await mutateAsync({ body: { data_retention_days: days } })
    } catch {
      setSaveError('Your data retention period could not be saved. Try again.')
      return
    }
    queryClient.setQueryData(getUserUsersMeGetQueryKey(), updatedUser)
    void queryClient.invalidateQueries({
      queryKey: getUserUsersMeGetQueryKey(),
    })
    setSavedDays(updatedUser.data_retention_days)
    form.reset(retentionValues(updatedUser.data_retention_days))
    setSuccess('Data retention period updated')
  }

  return (
    <>
      <GovukBackLink />
      {(error || success) && (
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            {error && (
              <GovukErrorSummary
                ref={errorRef}
                tabIndex={-1}
                errorList={[
                  {
                    href: validationError ? '#customDays' : '#save-retention',
                    text: error,
                  },
                ]}
                onClick={(event) => {
                  if (event.target instanceof HTMLAnchorElement) {
                    event.preventDefault()
                    document
                      .getElementById(
                        validationError ? 'customDays' : 'save-retention'
                      )
                      ?.focus()
                  }
                }}
              />
            )}
            {success && (
              <div ref={successRef} tabIndex={-1}>
                <GovukNotificationBanner
                  variant="success"
                  titleId="settings-success-title"
                >
                  <GovukHeading
                    as="h2"
                    size="m"
                    className="govuk-notification-banner__heading"
                  >
                    {success}
                  </GovukHeading>
                </GovukNotificationBanner>
              </div>
            )}
          </div>
        </div>
      )}
      <GovukHeading>Settings</GovukHeading>
      <section aria-labelledby="account-heading" className="govuk-grid-row">
        <div className="govuk-grid-column-two-thirds">
          <GovukHeading as="h2" size="m" id="account-heading">
            Account details
          </GovukHeading>
          <GovukTable>
            <GovukTableBody>
              <GovukTableRow>
                <GovukTableHeaderCell scope="row">Name</GovukTableHeaderCell>
                <GovukTableCell>{user.name ?? 'Not provided'}</GovukTableCell>
              </GovukTableRow>
              <GovukTableRow>
                <GovukTableHeaderCell scope="row">
                  User role
                </GovukTableHeaderCell>
                <GovukTableCell>
                  {user.roles.map((role) => roleLabels[role]).join(', ') ||
                    'No roles assigned'}
                </GovukTableCell>
              </GovukTableRow>
            </GovukTableBody>
          </GovukTable>
        </div>
      </section>
      <form
        onSubmit={form.handleSubmit(saveRetention)}
        noValidate
        className="govuk-!-margin-top-4"
      >
        <GovukFieldset disabled={isPending} aria-describedby="retention-hint">
          <GovukLegend size="m">
            <GovukHeading as="h2" size="m" className="govuk-!-margin-bottom-0">
              Data retention period
            </GovukHeading>
          </GovukLegend>
          <GovukHint id="retention-hint">
            After this period since they were created, your recordings,
            transcripts and documents will be deleted
          </GovukHint>
          <GovukFormGroup>
            <GovukRadios
              name="period"
              value={period}
              disabled={isPending}
              onChange={(value) => {
                clearFeedback()
                form.setValue('period', value, { shouldDirty: true })
              }}
              options={[
                { label: '7 days', value: '7' },
                { label: '14 days', value: '14' },
                { label: '30 days', value: '30' },
                {
                  label: 'Custom',
                  value: 'custom',
                  conditional: (
                    <GovukFormGroup hasError={!!validationError}>
                      <GovukLabel
                        htmlFor="customDays"
                        className="govuk-visually-hidden"
                      >
                        Custom period in days
                      </GovukLabel>
                      <GovukHint id="customDays-hint">
                        Enter the number of days, up to 30 - for example, 15
                      </GovukHint>
                      {validationError && (
                        <p
                          className="govuk-error-message"
                          id="customDays-error"
                        >
                          <span className="govuk-visually-hidden">Error:</span>{' '}
                          {validationError}
                        </p>
                      )}
                      <GovukInput
                        id="customDays"
                        inputMode="numeric"
                        className="govuk-input--width-10"
                        aria-invalid={!!validationError}
                        aria-describedby={`customDays-hint${validationError ? ' customDays-error' : ''}`}
                        {...form.register('customDays', {
                          onChange: clearFeedback,
                        })}
                      />
                    </GovukFormGroup>
                  ),
                },
              ]}
            />
          </GovukFormGroup>
        </GovukFieldset>
        <GovukButton
          id="save-retention"
          type="submit"
          variant={
            isPending || !!validationError || days === savedDays
              ? 'secondary'
              : 'primary'
          }
          disabled={isPending || !!validationError || days === savedDays}
        >
          {isPending ? 'Saving retention period...' : 'Save retention period'}
        </GovukButton>
      </form>
      <GovukSectionBreak size="l" />
      <MicrophoneSettings userId={user.id} onSuccess={setSuccess} />
    </>
  )
}
