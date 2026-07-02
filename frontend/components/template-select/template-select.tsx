import { TemplateRadioGroup } from '@/components/template-select/template-radio-group'
import { GovukDetails } from '@/components/govuk'
import {
  getTemplatesTemplatesGetOptions,
  getUserTemplatesUserTemplatesGetOptions,
} from '@/lib/client/@tanstack/react-query.gen'
import { Template } from '@/types/templates'
import { useQuery } from '@tanstack/react-query'

export const TemplateSelect = ({
  value,
  onChange,
}: {
  onChange: (template: Template) => void
  value: Template
}) => {
  return (
    <>
      <GovukDetails summary="General templates" open>
        <DefaultTemplateSelect value={value} onChange={onChange} />
      </GovukDetails>
      <GovukDetails summary="Your templates">
        <UserTemplateSelect value={value} onChange={onChange} />
      </GovukDetails>
    </>
  )
}

export const DefaultTemplateSelect = ({
  onChange,
  value,
}: {
  onChange: (template: Template) => void
  value: Template
}) => {
  const { data: templates = [], isLoading: isLoadingTemplates } = useQuery(
    getTemplatesTemplatesGetOptions()
  )
  return (
    <TemplateRadioGroup
      name="template"
      templates={templates.map((t) => ({
        id: `DEFAULT::${t.name}`,
        name: t.name,
        description: t.description,
      }))}
      onChange={(id) => {
        const selectedTemplate = templates.find(
          (t) => `DEFAULT::${t.name}` === id
        )
        if (selectedTemplate) {
          onChange({
            id: null,
            name: selectedTemplate.name,
            agenda_usage: selectedTemplate.agenda_usage,
          })
        }
      }}
      value={`DEFAULT::${value?.name}`}
      isLoading={isLoadingTemplates}
    />
  )
}

export const UserTemplateSelect = ({
  onChange,
  value,
}: {
  onChange: (template: Template) => void
  value: Template
}) => {
  const { data: templates = [], isLoading } = useQuery(
    getUserTemplatesUserTemplatesGetOptions()
  )
  if (!isLoading && !templates.length) {
    return (
      <p className="govuk-body">
        You haven&apos;t made any templates yet. Go to Templates to create and
        edit your templates.
      </p>
    )
  }
  return (
    <TemplateRadioGroup
      name="template"
      templates={templates.map((t) => ({
        id: t.id!,
        name: t.name,
        description: t.description || '',
      }))}
      onChange={(id) => {
        const selectedTemplate = templates.find((t) => t.id === id)
        if (selectedTemplate) {
          onChange({
            id: selectedTemplate.id!,
            name: selectedTemplate.name,
            agenda_usage: 'not_used',
          })
        }
      }}
      value={value?.id!}
      isLoading={isLoading}
    />
  )
}
