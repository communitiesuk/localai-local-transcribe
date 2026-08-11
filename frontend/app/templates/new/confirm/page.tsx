'use client'

import { ConfirmationInterstitial } from '@/components/confirmation-interstitial'
import { GovukNotificationBanner } from '@/components/govuk'
import {
  CreateUserTemplateRequest,
  createUserTemplateUserTemplatesPost,
} from '@/lib/client'
import { getUserTemplatesUserTemplatesGetQueryKey } from '@/lib/client/@tanstack/react-query.gen'
import { useBannerStore } from '@/stores/use-banner-store'
import { useTemplateCreateStore } from '@/stores/use-template-create-store'
import * as Sentry from '@sentry/nextjs'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import posthog from 'posthog-js'
import { useEffect, useState } from 'react'

const CONFLICT_STATUS = 409

class TemplateTitleConflictError extends Error {}

export default function CreateTemplateConfirmPage() {
  const router = useRouter()
  const draft = useTemplateCreateStore((store) => store.draft)
  const setTitleConflict = useTemplateCreateStore(
    (store) => store.setTitleConflict
  )
  const clear = useTemplateCreateStore((store) => store.clear)
  const setBanner = useBannerStore((store) => store.setBanner)
  const queryClient = useQueryClient()
  const [hasUnexpectedError, setHasUnexpectedError] = useState(false)

  const { mutate, isPending, isSuccess } = useMutation({
    mutationFn: async (body: CreateUserTemplateRequest) => {
      const { response } = await createUserTemplateUserTemplatesPost({
        body,
        throwOnError: false,
      })
      if (response?.status === CONFLICT_STATUS) {
        throw new TemplateTitleConflictError()
      }
      if (!response?.ok) {
        throw new Error('Failed to create template')
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: getUserTemplatesUserTemplatesGetQueryKey(),
      })
      setBanner({
        variant: 'success',
        title: 'Success',
        message: `'${draft?.name}' created`,
      })
      posthog.capture('template_created')
      clear()
      router.push('/templates')
    },
    onError: (error) => {
      if (error instanceof TemplateTitleConflictError) {
        setTitleConflict(true)
        router.back()
        return
      }
      Sentry.captureException(error)
      setHasUnexpectedError(true)
    },
  })

  // Nothing to create (direct navigation or a refresh) means there's no stashed
  // input, so return to the form. A successful create also clears the draft, but
  // it redirects to the list itself (isSuccess), so don't bounce to the form then.
  useEffect(() => {
    if (!draft && !isSuccess) router.replace('/templates/new')
  }, [draft, isSuccess, router])

  if (!draft) {
    return null
  }

  const handleCreate = () => {
    setHasUnexpectedError(false)
    mutate({
      ...draft,
      questions:
        draft.questions?.map((q, i) => ({ ...q, position: i })) ?? null,
    })
  }

  return (
    <>
      {hasUnexpectedError && (
        <GovukNotificationBanner
          variant="important"
          title="There is a problem"
          className="govuk-!-margin-bottom-6"
        >
          Something went wrong creating the template. Please try again.
        </GovukNotificationBanner>
      )}
      <ConfirmationInterstitial
        title={`Are you sure you want to create ‘${draft.name}’?`}
        actionLabel="Create template"
        actionVariant="primary"
        onAction={handleCreate}
        actionPending={isPending}
        cancelHref="/templates/new"
      >
        <p className="govuk-body">
          If you continue, you&apos;ll be able to use this template to create
          documents.
        </p>
      </ConfirmationInterstitial>
    </>
  )
}
