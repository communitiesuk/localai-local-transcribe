'use client'

import { GovukLabel } from '@/components/govuk'
import { TemplateType } from '@/lib/client'
import { cn } from '@/lib/utils'
import { FileSpreadsheet, FileType } from 'lucide-react'

export const TemplateTypeSelect = ({
  value,
  onChange,
}: {
  value: TemplateType | undefined
  onChange: (v: TemplateType) => void
}) => (
  <div className="govuk-form-group govuk-!-margin-bottom-6">
    <div className="grid grid-cols-2 gap-4" data-module="govuk-radios">
      {(
        [
          {
            id: 'template-type-document',
            radioValue: 'document' as TemplateType,
            icon: <FileType size={44} aria-hidden="true" />,
            label: 'Document',
            hint: 'Design how your minutes should look.',
          },
          {
            id: 'template-type-form',
            radioValue: 'form' as TemplateType,
            icon: <FileSpreadsheet size={44} aria-hidden="true" />,
            label: 'Form',
            hint: 'For complex question-answer type summarisation.',
          },
        ] as const
      ).map(({ id, radioValue, icon, label, hint }) => (
        <label
          key={radioValue}
          htmlFor={id}
          className={cn(
            'flex cursor-pointer items-start gap-4 rounded border-2 p-4 transition-colors',
            value === radioValue
              ? 'border-[#1d70b8] bg-blue-50'
              : 'border-[#b1b4b6] bg-white hover:border-[#505a5f]'
          )}
        >
          <input
            className="govuk-radios__input mt-1 shrink-0"
            id={id}
            name="templateType"
            type="radio"
            value={radioValue}
            checked={value === radioValue}
            onChange={() => onChange(radioValue)}
          />
          <div className="flex flex-col gap-2">
            {icon}
            <GovukLabel
              htmlFor={id}
              className="govuk-radios__label govuk-!-font-weight-bold govuk-!-margin-bottom-1 cursor-pointer"
            >
              {label}
            </GovukLabel>
            <p className="govuk-hint govuk-!-margin-bottom-0">{hint}</p>
          </div>
        </label>
      ))}
    </div>
  </div>
)
