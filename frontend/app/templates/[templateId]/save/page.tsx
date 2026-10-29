'use client'

import { ConfirmationInterstitial } from '@/components/confirmation-interstitial'
import { GovukWarningText, GovukNotificationBanner } from '@/components/govuk'
import {
  PatchUserTemplateRequest,
  editUserTemplateUserTemplatesTemplateIdPatch,
} from '@/lib/client'
import {
  getUserTemplatesUserTemplatesGetQueryKey,
  getUserTemplateUserTemplatesTemplateIdGetQueryKey,
} from '@/lib/client/@tanstack/react-query.gen'
import { useBannerStore } from '@/stores/use-banner-store'
import { useTemplateDraftStore } from '@/stores/use-template-draft-store'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { use, useEffect, useState, useRef } from 'react'

const CONFLICT_STATUS = 409

class TemplateTitleConflictError extends Error {}

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
  const [hasUnexpectedError, setHasUnexpectedError] = useState(false)
  const setTitleConflict = useTemplateDraftStore(
    (store) => store.setTitleConflict
  )

  const data = draft?.templateId === templateId ? draft.data : null

  const { mutate, isPending } = useMutation({
    mutationFn: async (body: PatchUserTemplateRequest) => {
      const { response } = await editUserTemplateUserTemplatesTemplateIdPatch({
        path: { template_id: templateId },
        body,
        throwOnError: false,
      })
      if (response?.status === CONFLICT_STATUS) {
        throw new TemplateTitleConflictError()
      }
      if (!response?.ok) {
        throw new Error('Failed to save template')
      }
    },
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
      clearDraft()
      router.push('/templates')
    },
    onError: (error) => {
      if (error instanceof TemplateTitleConflictError) {
        setTitleConflict(true)
        router.back()
        return
      }

      setHasUnexpectedError(true)
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
    setHasUnexpectedError(false)
    mutate({
      ...data,
      questions:
        data.type === 'form' && data.questions
          ? data.questions.map((q, i) => ({ ...q, position: i }))
          : null,
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
          Something went wrong saving the template. Please try again.
        </GovukNotificationBanner>
      )}

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
    </>
  )
}
