'use client'

import { ConfirmationInterstitial } from '@/components/confirmation-interstitial'
import { ProcessingSpinner } from '@/components/processing-spinner'
import useTemplateName from '@/app/templates/components/use-template-name'
import {
  duplicateUserTemplateUserTemplatesTemplateIdDuplicatePostMutation,
  getUserTemplatesUserTemplatesGetQueryKey,
} from '@/lib/client/@tanstack/react-query.gen'
import { useBannerStore } from '@/stores/use-banner-store'
import { useTemplateDraftStore } from '@/stores/use-template-draft-store'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Loader2 } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { use } from 'react'

const PENDING_LABEL = 'Duplicating template'

export default function DuplicateTemplatePage(props: {
  params: Promise<{ templateId: string }>
}) {
  const { templateId } = use(props.params)
  const router = useRouter()
  const clearDraft = useTemplateDraftStore((store) => store.clearDraft)
  const setBanner = useBannerStore((store) => store.setBanner)
  const queryClient = useQueryClient()

  const name = useTemplateName(templateId)

  const { mutate, isPending, isSuccess } = useMutation({
    ...duplicateUserTemplateUserTemplatesTemplateIdDuplicatePostMutation(),
    onSuccess: (duplicatedTemplate) => {
      queryClient.invalidateQueries({
        queryKey: getUserTemplatesUserTemplatesGetQueryKey(),
      })
      setBanner({
        variant: 'success',
        title: 'Success',
        message: `‘${duplicatedTemplate.name}’ created`,
      })
      clearDraft()
      router.push('/templates')
    },
  })

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
      title={`Are you sure you want to duplicate ‘${name}’?`}
      actionLabel="Continue"
      actionVariant="primary"
      onAction={() => mutate({ path: { template_id: templateId } })}
      actionPending={isPending}
      pendingLabel={PENDING_LABEL}
      cancelHref={`/templates/${templateId}`}
    >
      <p className="govuk-body">
        The duplicate will appear with a unique title based on {`‘${name}’`}
        until you change its title.
      </p>
    </ConfirmationInterstitial>
  )
}
