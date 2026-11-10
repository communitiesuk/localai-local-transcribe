'use client'

import { ConfirmationInterstitial } from '@/components/confirmation-interstitial'
import { ProcessingSpinner } from '@/components/processing-spinner'
import useTemplateName from '@/app/templates/components/use-template-name'
import { GovukWarningText } from '@/components/govuk'
import {
  deleteUserTemplateUserTemplatesTemplateIdDeleteMutation,
  getUserTemplatesUserTemplatesGetQueryKey,
} from '@/lib/client/@tanstack/react-query.gen'
import { useBannerStore } from '@/stores/use-banner-store'
import { useTemplateDraftStore } from '@/stores/use-template-draft-store'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Loader2 } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { use } from 'react'

const PENDING_LABEL = 'Deleting template'

export default function DeleteTemplatePage(props: {
  params: Promise<{ templateId: string }>
}) {
  const { templateId } = use(props.params)
  const router = useRouter()
  const clearDraft = useTemplateDraftStore((store) => store.clearDraft)
  const setBanner = useBannerStore((store) => store.setBanner)
  const queryClient = useQueryClient()

  const name = useTemplateName(templateId)

  const { mutate, isPending, isSuccess } = useMutation({
    ...deleteUserTemplateUserTemplatesTemplateIdDeleteMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: getUserTemplatesUserTemplatesGetQueryKey(),
      })
      setBanner({
        variant: 'important',
        title: 'Template deleted',
        message: `‘${name}’ deleted`,
      })
      clearDraft()
      router.push('/templates')
    },
  })

  // Hold the spinner until the app has finished navigating away.
  if (isSuccess) {
    return (
      <ProcessingSpinner label={PENDING_LABEL} message={`${PENDING_LABEL}…`} />
    )
  }

  if (name === undefined) {
    return (
      <div className="govuk-body flex items-center gap-2">
        <Loader2 className="animate-spin" aria-hidden="true" />
        Loading template…
      </div>
    )
  }

  return (
    <ConfirmationInterstitial
      title={`Are you sure you want to delete ‘${name}’?`}
      actionLabel="Delete"
      actionVariant="warning"
      onAction={() => mutate({ path: { template_id: templateId } })}
      actionPending={isPending}
      pendingLabel={PENDING_LABEL}
      cancelHref={`/templates/${templateId}`}
    >
      <GovukWarningText>
        If you proceed, you will not be able to recover this template.
      </GovukWarningText>
    </ConfirmationInterstitial>
  )
}
