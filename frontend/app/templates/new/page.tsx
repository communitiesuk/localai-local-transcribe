'use client'

import { FormTemplateEditor } from '@/app/templates/components/form-template-editor'
import { GovukHeading } from '@/components/govuk'
import {
  createUserTemplateUserTemplatesPostMutation,
  getUserTemplatesUserTemplatesGetOptions,
} from '@/lib/client/@tanstack/react-query.gen'
import { formatCurrentDateTime } from '@/lib/utils'
import { useBannerStore } from '@/stores/use-banner-store'
import { TemplateData } from '@/types/templates'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import posthog from 'posthog-js'
import { FormProvider, useForm } from 'react-hook-form'

export default function NewTemplatePage() {
  const form = useForm<TemplateData>({
    defaultValues: {
      name: '',
      description: '',
      content: '',
      heading: '',
      type: 'form',
      questions: [
        { title: '', description: '', format_instructions: '', position: 0 },
      ],
    },
  })
  const router = useRouter()
  const setBanner = useBannerStore((store) => store.setBanner)
  const { data: templates = [] } = useQuery(
    getUserTemplatesUserTemplatesGetOptions()
  )
  const { mutateAsync: saveTemplate } = useMutation({
    ...createUserTemplateUserTemplatesPostMutation(),
    onSuccess: () => {
      setBanner({
        variant: 'success',
        title: 'Success',
        message: `Template '${form.getValues('name')}' was successfully created at ${formatCurrentDateTime()}`,
      })
      posthog.capture('template_created')
      router.push('/templates')
    },
  })

  const onSubmit = async (data: TemplateData) => {
    const titleTaken = templates.some(
      (t) => t.name.trim().toLowerCase() === data.name.trim().toLowerCase()
    )
    if (titleTaken) {
      form.setError('name', {
        message: 'A template with this title already exists',
      })
      return
    }
    await saveTemplate({
      body: {
        name: data.name,
        description: data.description,
        content: data.content,
        type: data.type,
        // heading and question format_instructions are captured in the form; wire them here once the backend supports them
        questions:
          data.questions?.map((q, i) => ({
            position: i,
            title: q.title,
            description: q.description,
          })) ?? null,
      },
    })
  }

  return (
    <FormProvider {...form}>
      <GovukHeading as="h1" size="l" className="govuk-!-margin-bottom-6">
        Create template
      </GovukHeading>
      <FormTemplateEditor onSubmit={onSubmit} submitLabel="Create template" />
    </FormProvider>
  )
}
