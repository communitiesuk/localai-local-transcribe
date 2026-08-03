'use client'

import { DocumentTemplateEditor } from '@/app/templates/components/document-template-editor'
import { FormTemplateEditor } from '@/app/templates/components/form-template-editor'
import {
  editUserTemplateUserTemplatesTemplateIdPatchMutation,
  getUserTemplateUserTemplatesTemplateIdGetOptions,
  getUserTemplateUserTemplatesTemplateIdGetQueryKey,
} from '@/lib/client/@tanstack/react-query.gen'
import { formatCurrentDateTime } from '@/lib/utils'
import { useBannerStore } from '@/stores/use-banner-store'
import { TemplateData } from '@/types/templates'
import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query'
import { Loader2 } from 'lucide-react'
import { useRouter } from 'next/navigation'
import posthog from 'posthog-js'
import { useEffect, use } from 'react'
import { FormProvider, useForm } from 'react-hook-form'

export default function EditTemplatePage(props: {
  params: Promise<{ templateId: string }>
}) {
  const params = use(props.params)
  const { templateId } = params

  const { data: template } = useQuery({
    ...getUserTemplateUserTemplatesTemplateIdGetOptions({
      path: { template_id: templateId },
    }),
    placeholderData: keepPreviousData,
  })

  if (!template) {
    return (
      <>
        <header className="govuk-!-margin-bottom-6">
          <h1 className="govuk-heading-xl govuk-!-margin-bottom-0">
            Edit template
          </h1>
        </header>
        <div className="govuk-body flex items-center gap-2">
          <Loader2 className="animate-spin" aria-hidden="true" />
          Loading template…
        </div>
      </>
    )
  }

  return (
    <>
      <header className="govuk-!-margin-bottom-6">
        <h1 className="govuk-heading-xl govuk-!-margin-bottom-0">
          Edit template
        </h1>
      </header>
      <TemplateEditorForm
        templateId={templateId}
        defaultValues={{
          name: template.name,
          description: template.description,
          questions: template.questions,
          type: template.type,
          content: template.content,
        }}
      />
    </>
  )
}

const TemplateEditorForm = ({
  defaultValues,
  templateId,
}: {
  defaultValues: TemplateData
  templateId: string
}) => {
  const form = useForm<TemplateData>({ defaultValues })

  useEffect(() => {
    if (form.formState.isSubmitSuccessful) {
      form.reset(form.getValues(), { keepValues: true })
    }
  }, [form, form.formState.isSubmitSuccessful])

  const router = useRouter()
  const setBanner = useBannerStore((store) => store.setBanner)
  const queryClient = useQueryClient()
  const { mutate } = useMutation({
    ...editUserTemplateUserTemplatesTemplateIdPatchMutation(),
    onSuccess: () => {
      setBanner({
        variant: 'success',
        title: 'Success',
        message: `Template '${form.getValues('name')}' was successfully saved at ${formatCurrentDateTime()}`,
      })
      queryClient.invalidateQueries({
        queryKey: getUserTemplateUserTemplatesTemplateIdGetQueryKey({
          path: { template_id: templateId },
        }),
      })
      posthog.capture('template_edited')
      router.push('/templates')
    },
  })

  if (defaultValues.type === 'document') {
    return (
      <FormProvider {...form}>
        <DocumentTemplateEditor
          onSubmit={(data) =>
            mutate({
              path: { template_id: templateId },
              body: { ...data, questions: null },
            })
          }
        />
      </FormProvider>
    )
  }

  if (defaultValues.type === 'form') {
    return (
      <FormProvider {...form}>
        <FormTemplateEditor
          onSubmit={(data) =>
            mutate({
              path: { template_id: templateId },
              body: {
                ...data,
                questions:
                  data.questions?.map((q, i) => ({
                    ...q,
                    position: i,
                  })) || null,
              },
            })
          }
        />
      </FormProvider>
    )
  }
}
