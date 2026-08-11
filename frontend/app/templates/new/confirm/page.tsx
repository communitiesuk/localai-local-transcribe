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
import { Loader2 } from 'lucide-react'
import { useRouter } from 'next/navigation'
import posthog from 'posthog-js'
import { useEffect, useRef, useState } from 'react'

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
  const submitInProgress = useRef(false)
  const [hasUnexpectedError, setHasUnexpectedError] = useState(false)

  const { mutate, isPending } = useMutation({
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

  // Without the stashed input there is nothing to create; return to the form.
  useEffect(() => {
    if (submitInProgress.current) return
    if (!draft) router.replace('/templates/new')
  }, [draft, router])

  if (!draft) {
    return <Loader2 className="animate-spin" aria-hidden="true" />
  }

  const handleCreate = () => {
    submitInProgress.current = true
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
