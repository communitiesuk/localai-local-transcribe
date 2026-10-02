'use client'

import { DocumentTemplateEditor } from '@/app/templates/components/document-template-editor'
import { FormTemplateEditor } from '@/app/templates/components/form-template-editor'
import {
  TemplateEditorActions,
  useTemplateInterstitialActions,
} from '@/app/templates/components/template-editor-actions'
import { getUserTemplateUserTemplatesTemplateIdGetOptions } from '@/lib/client/@tanstack/react-query.gen'
import { useTemplateDraftStore } from '@/stores/use-template-draft-store'
import { TemplateData } from '@/types/templates'
import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { Loader2 } from 'lucide-react'
import { use, useEffect } from 'react'
import { FormProvider, useForm, useFormContext } from 'react-hook-form'
import { useLockNavigationContext } from '@/hooks/use-lock-navigation-context'

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
          content: template.content,
          heading: template.heading,
          questions: template.questions,
          type: template.type,
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
  const draft = useTemplateDraftStore((store) => store.draft)

  const form = useForm<TemplateData>({
    defaultValues: defaultValues,
  })

  // Re-hydrate any unsaved edits that were stashed prior to a confirmation
  // interstitial, so cancelling one returns here with all edits preserved.
  useEffect(() => {
    if (draft?.templateId === templateId) {
      form.reset(draft.data, { keepDefaultValues: true })
    }
  }, [draft, templateId, form])

  return (
    <FormProvider {...form}>
      <EditTemplateBody templateId={templateId} type={defaultValues.type} />
    </FormProvider>
  )
}

const EditTemplateBody = ({
  templateId,
  type,
}: {
  templateId: string
  type: TemplateData['type']
}) => {
  const { goToSave, goToCancel } = useTemplateInterstitialActions(templateId)
  const actions = <TemplateEditorActions templateId={templateId} />
  const form = useFormContext<TemplateData>()

  const { setLockNavigation } = useLockNavigationContext()

  useEffect(() => {
    if (!form.formState.isDirty) {
      setLockNavigation(false)
      return
    }
    setLockNavigation(() => (href: string) => {
      goToCancel(href)
    })

    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      e.preventDefault()
      e.returnValue = true
    }
    window.addEventListener('beforeunload', handleBeforeUnload)

    return () => {
      setLockNavigation(false)
      window.removeEventListener('beforeunload', handleBeforeUnload)
    }
  }, [form.formState.isDirty, goToCancel, setLockNavigation])

  if (type === 'document') {
    return <DocumentTemplateEditor onSubmit={goToSave} actions={actions} />
  }

  if (type === 'form') {
    return <FormTemplateEditor onSubmit={goToSave} actions={actions} />
  }
}
