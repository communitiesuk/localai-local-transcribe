'use client'

import {
  GovukBackLink,
  GovukButton,
  GovukFieldset,
  GovukFormGroup,
  GovukHint,
  GovukLegend,
  GovukRadios,
} from '@/components/govuk'
import { GetUserResponse } from '@/lib/client'
import {
  getUserUsersMeGetOptions,
  getUserUsersMeGetQueryKey,
  updateDataRetentionUsersDataRetentionPatchMutation,
} from '@/lib/client/@tanstack/react-query.gen'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Loader2 } from 'lucide-react'
import { useCallback } from 'react'
import { Controller, useForm } from 'react-hook-form'

type UserSettingsForm = { dataRetention: 'none' | `${number}` }

export default function SettingsPage() {
  const { data: user } = useQuery({ ...getUserUsersMeGetOptions() })

  if (!user) {
    return (
      <div className="govuk-body mx-auto flex max-w-3xl items-center gap-2 pt-1">
        <Loader2 className="animate-spin" />
        Loading...
      </div>
    )
  }

  return (
    <div className="govuk-grid-row">
      <div className="govuk-grid-column-two-thirds">
        <GovukBackLink />
        <h1 className="govuk-heading-xl">Settings</h1>
        <p className="govuk-body">Configure your account settings</p>
        <SettingsForm user={user} />
      </div>
    </div>
  )
}

function SettingsForm({ user }: { user: GetUserResponse }) {
  const form = useForm<UserSettingsForm>({
    defaultValues: {
      dataRetention: user.data_retention_days
        ? `${user.data_retention_days}`
        : 'none',
    },
  })
  const queryClient = useQueryClient()
  const { mutateAsync, isPending } = useMutation({
    ...updateDataRetentionUsersDataRetentionPatchMutation(),
  })

  const onSubmit = useCallback(
    async (data: UserSettingsForm) => {
      await mutateAsync(
        {
          body: {
            data_retention_days:
              data.dataRetention === 'none' ? null : Number(data.dataRetention),
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
    [mutateAsync, queryClient]
  )

  return (
    <form
      onSubmit={form.handleSubmit(onSubmit)}
      className="govuk-!-margin-top-6"
    >
      <GovukFormGroup>
        <GovukFieldset aria-describedby="dataRetention-hint">
          <GovukLegend size="m">Data Retention Period</GovukLegend>
          <GovukHint id="dataRetention-hint">
            After this period the transcriptions, minutes and audio recording
            will be permanently deleted.
          </GovukHint>
          <Controller
            control={form.control}
            name="dataRetention"
            render={({ field: { onChange, value, ref, disabled } }) => (
              <GovukRadios
                name="dataRetention"
                value={value}
                onChange={onChange}
                disabled={disabled}
                ref={ref}
                options={[
                  { label: 'Keep indefinitely', value: 'none' },
                  { label: '1 day', value: '1' },
                  { label: '7 days', value: '7' },
                  { label: '30 days', value: '30' },
                  { label: '90 days', value: '90' },
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
            'Save'
          )}
        </GovukButton>
      </div>
    </form>
  )
}
