'use client'

import { FormTemplateEditor } from '@/app/templates/components/form-template-editor'
import { GovukButton, GovukButtonGroup, GovukHeading } from '@/components/govuk'
import { useTemplateCreateStore } from '@/stores/use-template-create-store'
import { TemplateData } from '@/types/templates'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'
import { FormProvider, useForm } from 'react-hook-form'

const EMPTY_TEMPLATE: TemplateData = {
  name: '',
  description: '',
  content: '',
  heading: '',
  type: 'form',
  questions: [
    { title: '', description: '', format_instructions: '', position: 0 },
  ],
}

export default function NewTemplatePage() {
  const router = useRouter()
  const draft = useTemplateCreateStore((store) => store.draft)
  const titleConflict = useTemplateCreateStore((store) => store.titleConflict)
  const setDraft = useTemplateCreateStore((store) => store.setDraft)
  const setTitleConflict = useTemplateCreateStore(
    (store) => store.setTitleConflict
  )

  const form = useForm<TemplateData>({
    // Re-hydrate input stashed before the confirmation interstitial, so
    // cancelling it returns here with everything intact.
    defaultValues: draft ?? EMPTY_TEMPLATE,
  })

  // If the interstitial returned back with a duplicate-title rejection, flag
  // it on the field, then consume it so it doesn't reappear.
  useEffect(() => {
    if (!titleConflict) return
    form.setError('name', {
      message: 'A template with this title already exists',
    })
    setTitleConflict(false)
  }, [titleConflict, form, setTitleConflict])

  const onSubmit = (data: TemplateData) => {
    setDraft(data)
    router.push('/templates/new/confirm')
  }

  const onCancel = () => {
    setDraft(form.getValues())
    router.push('/templates/new/discard')
  }

  const actions = (
    <div>
      <hr className="govuk-section-break govuk-section-break--visible govuk-!-margin-bottom-6" />
      <GovukButtonGroup>
        <GovukButton type="submit" className="govuk-!-margin-bottom-0">
          Create template
        </GovukButton>
        <GovukButton variant="link" onClick={onCancel}>
          Cancel
        </GovukButton>
      </GovukButtonGroup>
    </div>
  )

  return (
    <FormProvider {...form}>
      <GovukHeading as="h1" size="l" className="govuk-!-margin-bottom-6">
        Create template
      </GovukHeading>
      <FormTemplateEditor onSubmit={onSubmit} actions={actions} />
    </FormProvider>
  )
}
