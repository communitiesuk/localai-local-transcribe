'use client'

import { FormTemplateEditor } from '@/app/templates/components/form-template-editor'
import { GovukHeading, GovukNotificationBanner } from '@/components/govuk'
import {
  CreateUserTemplateRequest,
  createUserTemplateUserTemplatesPost,
} from '@/lib/client'
import { useBannerStore } from '@/stores/use-banner-store'
import { TemplateData } from '@/types/templates'
import * as Sentry from '@sentry/nextjs'
import { useMutation } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import posthog from 'posthog-js'
import { useState } from 'react'
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
  const [hasUnexpectedError, setHasUnexpectedError] = useState(false)
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
        return
      }
      Sentry.captureException(error)
      setHasUnexpectedError(true)
    },
  })

  const onSubmit = async (data: TemplateData) => {
    setHasUnexpectedError(false)
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
      {hasUnexpectedError && (
        <GovukNotificationBanner
          variant="important"
          title="There is a problem"
          className="govuk-!-margin-bottom-6"
        >
          Something went wrong creating the template. Please try again.
        </GovukNotificationBanner>
      )}
      <GovukHeading as="h1" size="l" className="govuk-!-margin-bottom-6">
        Create template
      </GovukHeading>
      <FormTemplateEditor onSubmit={onSubmit} submitLabel="Create template" />
    </FormProvider>
  )
}
