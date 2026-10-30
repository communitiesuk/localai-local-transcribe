'use client'

import { ConfirmationInterstitial } from '@/components/confirmation-interstitial'
import { GovukWarningText } from '@/components/govuk'
import {
  editUserTemplateUserTemplatesTemplateIdPatchMutation,
  getUserTemplatesUserTemplatesGetQueryKey,
  getUserTemplateUserTemplatesTemplateIdGetQueryKey,
} from '@/lib/client/@tanstack/react-query.gen'
import { useBannerStore } from '@/stores/use-banner-store'
import { useTemplateDraftStore } from '@/stores/use-template-draft-store'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import posthog from 'posthog-js'
import { use, useEffect, useRef } from 'react'

export default function SaveTemplatePage(props: {
  params: Promise<{ templateId: string }>
}) {
  const { templateId } = use(props.params)
  const router = useRouter()
  const draft = useTemplateDraftStore((store) => store.draft)
  const clearDraft = useTemplateDraftStore((store) => store.clearDraft)
  const setBanner = useBannerStore((store) => store.setBanner)
  const queryClient = useQueryClient()
  const submitInProgress = useRef(false)

  const data = draft?.templateId === templateId ? draft.data : null

  const { mutate, isPending } = useMutation({
    ...editUserTemplateUserTemplatesTemplateIdPatchMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: getUserTemplatesUserTemplatesGetQueryKey(),
      })
      queryClient.removeQueries({
        queryKey: getUserTemplateUserTemplatesTemplateIdGetQueryKey({
          path: { template_id: templateId },
        }),
      })
      setBanner({
        variant: 'success',
        title: 'Success',
        message: `Changes to ‘${data?.name}’ saved`,
      })
      posthog.capture('template_edited')
      clearDraft()
      router.push('/templates')
    },
  })

  // No edited data (direct navigation or a refresh) means there's nothing to
  // save, so return to the editor as a fallback.
  useEffect(() => {
    if (!data && !submitInProgress.current) {
      router.replace(`/templates/${templateId}`)
    }
  }, [data, router, templateId])

  if (!data) {
    return null
  }

  const handleSave = () => {
    submitInProgress.current = true
    mutate({
      path: { template_id: templateId },
      body: {
        ...data,
        questions:
          data.type === 'form' && data.questions
            ? data.questions.map((q, i) => ({ ...q, position: i }))
            : null,
      },
    })
  }

  return (
    <ConfirmationInterstitial
      title={`Are you sure you want to save changes to ‘${data.name}’?`}
      actionLabel="Continue"
      actionVariant="primary"
      onAction={handleSave}
      actionPending={isPending}
      cancelHref={`/templates/${templateId}`}
    >
      <p className="govuk-body">
        If you continue, your changes will replace the existing version of ‘
        {data.name}’.
      </p>
      <GovukWarningText>
        You will not be able to undo these changes.
      </GovukWarningText>
    </ConfirmationInterstitial>
  )
}
