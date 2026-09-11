import { TemplateRadioGroup } from '@/components/template-select/template-radio-group'
import { GovukDetails } from '@/components/govuk'
import { templateValue, useTemplates } from '@/hooks/use-templates'
import type { SelectableTemplate } from '@/hooks/use-templates'
import type { Template } from '@/types/templates'

export const TemplateSelect = ({
  value,
  onChange,
}: {
  onChange: (template: Template) => void
  value: Template
}) => {
  const {
    sortedDefaultTemplates,
    sortedUserTemplates,
    isLoadingDefaultTemplates,
    isLoadingUserTemplates,
  } = useTemplates()

  return (
    <>
      <GovukDetails summary="General templates" open>
        <TemplateSelectGroup
          value={value}
          onChange={onChange}
          templates={sortedDefaultTemplates}
          isLoading={isLoadingDefaultTemplates}
        />
      </GovukDetails>
      <GovukDetails summary="Your templates">
        <TemplateSelectGroup
          value={value}
          onChange={onChange}
          templates={sortedUserTemplates}
          isLoading={isLoadingUserTemplates}
          emptyMessage="You haven't made any templates yet. Go to Templates to create and edit your templates."
        />
      </GovukDetails>
    </>
  )
}

const TemplateSelectGroup = ({
  onChange,
  value,
  templates,
  isLoading,
  emptyMessage,
}: {
  onChange: (template: Template) => void
  value: Template
  templates: SelectableTemplate[]
  isLoading: boolean
  emptyMessage?: string
}) => {
  if (!isLoading && !templates.length && emptyMessage) {
    return <p className="govuk-body">{emptyMessage}</p>
  }

  return (
    <TemplateRadioGroup
      name="template"
      templates={templates.map((t) => ({
        id: templateValue(t),
        name: t.name,
        description: t.description,
      }))}
      onChange={(id) => {
        const selectedTemplate = templates.find((t) => templateValue(t) === id)
        if (selectedTemplate) {
          onChange({
            id: selectedTemplate.id,
            name: selectedTemplate.name,
            agenda_usage: selectedTemplate.agenda_usage,
          })
        }
      }}
      value={value ? templateValue(value) : ''}
      isLoading={isLoading}
    />
  )
}
