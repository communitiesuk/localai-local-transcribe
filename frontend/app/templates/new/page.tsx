'use client'

import { DocumentTemplateEditor } from '@/app/templates/components/document-template-editor'
import { ExampleTemplatesDialog } from '@/app/templates/components/example-templates-dialog'
import { FormTemplateEditor } from '@/app/templates/components/form-template-editor'
import {
  exampleDocumentTemplates,
  exampleFormTemplates,
} from '@/app/templates/data/example-templates'
import { TemplateTypeSelect } from '@/app/templates/new/template-type-select'
import { GovukButton } from '@/components/govuk'
import { TemplateType } from '@/lib/client'
import { createUserTemplateUserTemplatesPostMutation } from '@/lib/client/@tanstack/react-query.gen'
import { TemplateData } from '@/types/templates'
import { useMutation } from '@tanstack/react-query'
import { ArrowRight } from 'lucide-react'
import { useRouter, useSearchParams } from 'next/navigation'
import posthog from 'posthog-js'
import { Suspense, useState } from 'react'
import { FormProvider, useForm, useWatch } from 'react-hook-form'
import { toast } from 'sonner'

function NewTemplateContent() {
  const [selectedType, setSelectedType] = useState<TemplateType | undefined>(
    undefined
  )
  const searchParams = useSearchParams()
  const templateTypeParam = searchParams.get('type')
  const templateExampleParam = searchParams.get('example')
  const foundExample = [
    ...exampleDocumentTemplates,
    ...exampleFormTemplates,
  ].find((v) => v.name == templateExampleParam)
  const form = useForm<TemplateData>({
    defaultValues: foundExample
      ? foundExample
      : {
          name: '',
          description: '',
          content: '',
          questions: [],
          type:
            templateTypeParam &&
            ['document', 'form'].includes(templateTypeParam)
              ? (templateTypeParam as TemplateType)
              : undefined,
        },
  })
  const navigation = useRouter()
  const { mutateAsync: saveTemplate } = useMutation({
    ...createUserTemplateUserTemplatesPostMutation(),
    onSuccess: () => {
      toast.success('Saved template!')
      posthog.capture('template_created')
      navigation.push('/templates')
    },
  })
  const onSubmit = async (data: TemplateData) => {
    await saveTemplate({
      body: {
        ...data,
        questions:
          data.type === 'form' && data.questions
            ? data.questions.map((q, i) => ({ ...q, position: i }))
            : null,
      },
    })
  }
  const templateType = useWatch({ name: 'type', control: form.control })
  const onSelectExample = (example: TemplateData) => {
    form.setValue('name', example.name, { shouldDirty: true })
    form.setValue('description', example.description, { shouldDirty: true })
    form.setValue('type', example.type, { shouldDirty: true })
    form.setValue('content', example.content, { shouldDirty: true })
    if (example.questions) {
      form.setValue('questions', example.questions, { shouldDirty: true })
    } else {
      form.setValue('questions', null, { shouldDirty: true })
    }
  }

  if (templateType == 'document') {
    return (
      <FormProvider {...form}>
        <header className="govuk-!-margin-bottom-6">
          <div className="govuk-!-margin-bottom-2 flex items-center gap-4">
            <h1 className="govuk-heading-xl govuk-!-margin-bottom-0">
              New template
            </h1>
            <ExampleTemplatesDialog
              onSelectTemplate={onSelectExample}
              examples={exampleDocumentTemplates}
            />
          </div>
          <p className="govuk-body govuk-hint">
            Design your minute template. You can describe a structure and
            provide style guidance. Try an example to get started.
          </p>
        </header>
        <DocumentTemplateEditor onSubmit={onSubmit} />
      </FormProvider>
    )
  }

  if (templateType == 'form') {
    return (
      <FormProvider {...form}>
        <header className="govuk-!-margin-bottom-6">
          <div className="govuk-!-margin-bottom-2 flex items-center gap-4">
            <h1 className="govuk-heading-xl govuk-!-margin-bottom-0">
              New template
            </h1>
            <ExampleTemplatesDialog
              onSelectTemplate={onSelectExample}
              examples={exampleFormTemplates}
            />
          </div>
          <p className="govuk-body govuk-hint">
            Design your minute template. You can describe a structure and
            provide style guidance. Try an example to get started.
          </p>
        </header>
        <FormTemplateEditor onSubmit={onSubmit} />
      </FormProvider>
    )
  }

  return (
    <div>
      <h2 className="govuk-heading-m">Template type</h2>
      <p className="govuk-body govuk-hint govuk-!-margin-bottom-4">
        Choose the type of template you would like to create.
      </p>
      <TemplateTypeSelect value={selectedType} onChange={setSelectedType} />
      <GovukButton
        type="button"
        onClick={() => {
          form.setValue('type', selectedType!)
        }}
        disabled={!selectedType}
        className="govuk-!-margin-bottom-0 flex items-center gap-2"
        isStartButton
      >
        Next <ArrowRight size={16} aria-hidden="true" />
      </GovukButton>
    </div>
  )
}

export default function Page() {
  return (
    <Suspense fallback={<div className="govuk-body">Loading…</div>}>
      <NewTemplateContent />
    </Suspense>
  )
}
