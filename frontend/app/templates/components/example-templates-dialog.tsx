'use client'

import { GovukButton } from '@/components/govuk'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTrigger,
} from '@/components/ui/dialog'
import { TemplateData } from '@/types/templates'
import { FileText } from 'lucide-react'
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
  const handleSelectExample = (template: TemplateData) => {
    onSelectTemplate(template)
    setOpen(false)
    posthog.capture('template_example_selected', {
      example_name: template.name,
    })
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild type="button">
        <GovukButton
          variant="secondary"
          className="govuk-!-margin-bottom-0 flex items-center gap-2"
        >
          <FileText className="h-4 w-4" />
          Try an example
        </GovukButton>
      </DialogTrigger>
      <DialogContent className="max-h-[80vh] min-w-3xl overflow-y-auto">
        <DialogHeader>
          <h2 className="govuk-heading-m govuk-!-margin-bottom-4">
            Choose an example template
          </h2>
        </DialogHeader>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          {examples.map((template, index) => (
            <div
              key={index}
              className="flex flex-col justify-between gap-4 rounded-lg border border-gray-200 bg-white p-4 shadow-sm"
            >
              <div>
                <h3 className="govuk-heading-s govuk-!-margin-bottom-1">
                  {template.name}
                </h3>
                <p className="govuk-body govuk-!-font-size-14 leading-normal text-gray-600">
                  {template.description}
                </p>
              </div>

              <div className="flex items-center gap-2">
                <GovukButton
                  type="button"
                  variant="secondary"
                  onClick={() => handleSelectExample(template)}
                  className="govuk-!-margin-bottom-0 w-full justify-center"
                >
                  Use this template
                </GovukButton>
              </div>
            </div>
          ))}
        </div>
      </DialogContent>
    </Dialog>
  )
}
