'use client'

import { ConfirmationInterstitial } from '@/components/confirmation-interstitial'
import { useTemplateCreateStore } from '@/stores/use-template-create-store'
import { useRouter } from 'next/navigation'
import { useDestination } from '@/hooks/use-destination'

export default function DiscardTemplatePage() {
  const router = useRouter()
  const clear = useTemplateCreateStore((store) => store.clear)

  const destination = useDestination('/templates')

  const handleDiscard = () => {
    clear()
    router.push(destination)
  }

  return (
    <ConfirmationInterstitial
      title="Are you sure you want to discard this template?"
      actionLabel="Discard"
      actionVariant="warning"
      onAction={handleDiscard}
      cancelHref="/templates/new"
    >
      <p className="govuk-body">
        If you continue, your template will not be saved.
      </p>
    </ConfirmationInterstitial>
  )
}
