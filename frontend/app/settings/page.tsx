'use client'

import {
  GovukBackLinkClient,
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
import { useRouter } from 'next/navigation'
import { useCallback } from 'react'
import { Controller, useForm } from 'react-hook-form'

type UserSettingsForm = { dataRetention: 'none' | `${number}` }

export default function SettingsPage() {
  const { data: user } = useQuery({ ...getUserUsersMeGetOptions() })
  const router = useRouter()

  if (!user) {
    return (
      <div className="mx-auto flex max-w-3xl items-center gap-2 pt-1 govuk-body">
        <Loader2 className="animate-spin" />
        Loading...
      </div>
    )
  }

  return (
    <div className="govuk-grid-row">
      <div className="govuk-grid-column-two-thirds">
        <GovukBackLinkClient onClick={() => router.back()} />
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
    <form onSubmit={form.handleSubmit(onSubmit)} className="govuk-!-margin-top-6">
      <GovukFormGroup>
        <GovukFieldset describedBy="dataRetention-hint">
          <GovukLegend size="m">Data Retention Period</GovukLegend>
          <GovukHint id="dataRetention-hint">
            After this period the transcriptions, minutes and audio recording will
            be permanently deleted.
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
              >
                <GovukRadios.Item value="none">
                  Keep indefinitely
                </GovukRadios.Item>
                <GovukRadios.Item value="1">1 day</GovukRadios.Item>
                <GovukRadios.Item value="7">7 days</GovukRadios.Item>
                <GovukRadios.Item value="30">30 days</GovukRadios.Item>
                <GovukRadios.Item value="90">90 days</GovukRadios.Item>
              </GovukRadios>
            )}
          />
        </GovukFieldset>
      </GovukFormGroup>

      <div className="govuk-!-margin-top-6">
        <GovukButton type="submit" isSubmitting={isPending}>
          Save
        </GovukButton>
      </div>
    </form>
  )
}
