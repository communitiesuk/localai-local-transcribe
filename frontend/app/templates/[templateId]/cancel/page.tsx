'use client'

import { ConfirmationInterstitial } from '@/components/confirmation-interstitial'
import { useTemplateDraftStore } from '@/stores/use-template-draft-store'
import { useRouter } from 'next/navigation'
import { use } from 'react'
import { useDestination } from '@/hooks/use-destination'

export default function CancelTemplateEditPage(props: {
  params: Promise<{ templateId: string }>
}) {
  const { templateId } = use(props.params)

  const destination = useDestination('/templates')

  const router = useRouter()
  const clearDraft = useTemplateDraftStore((store) => store.clearDraft)

  const handleDiscard = () => {
    clearDraft()
    router.push(destination)
  }

  return (
    <ConfirmationInterstitial
      title="Are you sure you want to discard your changes?"
      actionLabel="Discard"
      actionVariant="warning"
      onAction={handleDiscard}
      cancelHref={`/templates/${templateId}`}
    >
      <p className="govuk-body">
        If you continue, your changes to this template will not be saved.
      </p>
    </ConfirmationInterstitial>
  )
}
