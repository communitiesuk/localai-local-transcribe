'use client'

import { GovukRadios } from '@/components/govuk'

export const TemplateRadioGroup = ({
  name,
  value,
  onChange,
  templates,
  isLoading,
}: {
  name: string
  value: string
  onChange: (value: string) => void
  templates: { id: string; name: string; description: string }[]
  isLoading: boolean
}) => {
  if (isLoading) {
    return <p className="govuk-body">Loading templates...</p>
  }

  return (
    <GovukRadios
      name={name}
      value={value}
      onChange={onChange}
      options={templates.map((t) => ({
        label: t.name,
        value: t.id,
        hint: t.description,
      }))}
    />
  )
}
