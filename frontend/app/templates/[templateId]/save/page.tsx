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
import { redirect, useRouter } from 'next/navigation'
import posthog from 'posthog-js'
import { use } from 'react'

export default function SaveTemplatePage(props: {
  params: Promise<{ templateId: string }>
}) {
  const { templateId } = use(props.params)
  const router = useRouter()
  const draft = useTemplateDraftStore((store) => store.draft)
  const clearDraft = useTemplateDraftStore((store) => store.clearDraft)
  const setBanner = useBannerStore((store) => store.setBanner)
  const queryClient = useQueryClient()

  const data = draft?.templateId === templateId ? draft.data : null

  const { mutate, isPending, isSuccess } = useMutation({
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

  if (!data) {
    // A successful save clears the draft as it redirects to the list; render
    // nothing while that navigation completes. Otherwise there's nothing to save
    // (direct navigation or a refresh), so return to the editor.
    if (isSuccess) return null
    redirect(`/templates/${templateId}`)
  }

  const handleSave = () => {
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
