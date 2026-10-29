'use client'

import { ConfirmationInterstitial } from '@/components/confirmation-interstitial'
import { useTemplates } from '@/hooks/use-templates'
import {
  getUserTemplatesUserTemplatesGetQueryKey,
  duplicateDefaultTemplateTemplatesTemplateNameDuplicatePostMutation,
} from '@/lib/client/@tanstack/react-query.gen'
import { useBannerStore } from '@/stores/use-banner-store'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Loader2 } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { use } from 'react'

export default function DuplicateDefaultTemplatePage(props: {
  params: Promise<{ templateName: string }>
}) {
  const { templateName } = use(props.params)
  const templateId = decodeURIComponent(templateName)
  const { sortedDefaultTemplates, isLoading, isError } = useTemplates()
  const template = sortedDefaultTemplates.find(
    (defaultTemplate) => defaultTemplate.id === templateId
  )
  const name = template?.name ?? templateId
  const router = useRouter()
  const setBanner = useBannerStore((store) => store.setBanner)
  const queryClient = useQueryClient()

  const { mutate, isPending } = useMutation({
    ...duplicateDefaultTemplateTemplatesTemplateNameDuplicatePostMutation(),
    onSuccess: (duplicatedTemplate) => {
      queryClient.invalidateQueries({
        queryKey: getUserTemplatesUserTemplatesGetQueryKey(),
      })
      setBanner({
        variant: 'success',
        title: 'Success',
        message: `‘${duplicatedTemplate.name}’ created`,
      })
      router.push('/templates')
    },
  })

  if (isLoading) {
    return <Loader2 className="animate-spin" />
  }

  if (isError || !template) {
    return (
      <p className="govuk-body">
        Something went wrong fetching the template to duplicate.
      </p>
    )
  }

  return (
    <ConfirmationInterstitial
      title={`Are you sure you want to duplicate ‘${name}’?`}
      actionLabel="Continue"
      actionVariant="primary"
      onAction={() => mutate({ path: { template_name: templateId } })}
      actionPending={isPending}
      cancelHref="/templates"
    >
      <p className="govuk-body">
        The duplicate will appear in your templates with a unique title based on{' '}
        {`‘${name}’`} until you change its title.
      </p>
    </ConfirmationInterstitial>
  )
}
