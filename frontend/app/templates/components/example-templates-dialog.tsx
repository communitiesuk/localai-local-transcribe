'use client'

import { GovukButton, GovukRadios } from '@/components/govuk'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { TemplateData } from '@/types/templates'
import posthog from 'posthog-js'
import { useState } from 'react'

interface ExampleTemplatesDialogProps {
  onSelectTemplate: (template: TemplateData) => void
  examples: TemplateData[]
}

export function ExampleTemplatesDialog({
  onSelectTemplate,
  examples,
}: ExampleTemplatesDialogProps) {
  const [open, setOpen] = useState(false)
  const [selectedValue, setSelectedValue] = useState<string | undefined>(
    undefined
  )

  const handleUseTemplate = () => {
    const template = examples.find((e) => e.name === selectedValue)
    if (!template) return
    onSelectTemplate(template)
    setOpen(false)
    setSelectedValue(undefined)
    posthog.capture('template_example_selected', {
      example_name: template.name,
    })
  }

  const radioOptions = examples.map((template) => ({
    label: template.name,
    value: template.name,
    hint: template.description,
  }))

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        setOpen(next)
        if (!next) setSelectedValue(undefined)
      }}
    >
      <DialogTrigger asChild>
        <button
          type="button"
          className="govuk-link"
          style={{ color: 'var(--govuk-link-colour)' }}
        >
          Try an example
        </button>
      </DialogTrigger>
      <DialogContent className="max-h-[80vh] overflow-y-auto sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="govuk-heading-m govuk-!-margin-bottom-4">
            Try an example
          </DialogTitle>
        </DialogHeader>
        <GovukRadios
          name="example-template"
          value={selectedValue}
          onChange={setSelectedValue}
          options={radioOptions}
          className="govuk-!-margin-bottom-6"
        />
        <div className="flex gap-3">
          <GovukButton
            type="button"
            onClick={handleUseTemplate}
            disabled={!selectedValue}
            className="govuk-!-margin-bottom-0"
          >
            Use template
          </GovukButton>
          <GovukButton
            type="button"
            variant="secondary"
            className="govuk-!-margin-bottom-0"
            onClick={() => setOpen(false)}
          >
            Cancel
          </GovukButton>
        </div>
      </DialogContent>
    </Dialog>
  )
}
