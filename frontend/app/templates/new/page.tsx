'use client'

import { FormTemplateEditor } from '@/app/templates/components/form-template-editor'
import { GovukHeading } from '@/components/govuk'
import {
<<<<<<< HEAD
  CreateUserTemplateRequest,
  createUserTemplateUserTemplatesPost,
} from '@/lib/client'
=======
  exampleDocumentTemplates,
  exampleFormTemplates,
} from '@/app/templates/data/example-templates'
import { TemplateType } from '@/lib/client'
import { createUserTemplateUserTemplatesPostMutation } from '@/lib/client/@tanstack/react-query.gen'
>>>>>>> development
import { useBannerStore } from '@/stores/use-banner-store'
import { TemplateData } from '@/types/templates'
import { useMutation } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import posthog from 'posthog-js'
import { FormProvider, useForm } from 'react-hook-form'

const CONFLICT_STATUS = 409

export class TemplateTitleConflictError extends Error {}

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
  const { mutateAsync: saveTemplate } = useMutation({
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
      setBanner({
        variant: 'success',
        title: 'Success',
        message: `'${form.getValues('name')}' created`,
      })
      posthog.capture('template_created')
      router.push('/templates')
    },
    onError: (error) => {
      if (error instanceof TemplateTitleConflictError) {
        form.setError('name', {
          message: 'A template with this title already exists',
        })
      }
    },
  })

  const onSubmit = async (data: TemplateData) => {
    try {
      await saveTemplate({
        name: data.name,
        description: data.description,
        content: data.content,
        heading: data.heading,
        type: data.type,
        questions:
          data.questions?.map((q, i) => ({
            position: i,
            title: q.title,
            description: q.description,
            format_instructions: q.format_instructions,
          })) ?? null,
      })
    } catch {
      // Handled in onError above
    }
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
