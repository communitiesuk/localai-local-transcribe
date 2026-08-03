'use client'

import { cn } from '@/lib/utils'
import React from 'react'

type DateInputProps = {
  id: string
  legend: React.ReactNode
  hint?: React.ReactNode
  className?: string
} & Omit<React.HTMLAttributes<HTMLDivElement>, 'className' | 'id'>

const items = [
  { name: 'day', label: 'Day', width: 'govuk-input--width-2' },
  { name: 'month', label: 'Month', width: 'govuk-input--width-2' },
  { name: 'year', label: 'Year', width: 'govuk-input--width-4' },
] as const

export function GovukDateInput({
  id,
  legend,
  hint,
  className,
  ...rest
}: DateInputProps) {
  const hintId = hint ? `${id}-hint` : undefined

  return (
    <div className={cn('govuk-form-group', className)}>
      <fieldset
        className="govuk-fieldset"
        role="group"
        aria-describedby={hintId}
      >
        <legend className="govuk-fieldset__legend">{legend}</legend>
        {hint && (
          <div id={hintId} className="govuk-hint">
            {hint}
          </div>
        )}
        <div {...rest} className="govuk-date-input" id={id}>
          {items.map((item) => (
            <div key={item.name} className="govuk-date-input__item">
              <div className="govuk-form-group">
                <label
                  className="govuk-label govuk-date-input__label"
                  htmlFor={`${id}-${item.name}`}
                >
                  {item.label}
                </label>
                <input
                  className={cn(
                    'govuk-input govuk-date-input__input',
                    item.width
                  )}
                  id={`${id}-${item.name}`}
                  name={`${id}-${item.name}`}
                  type="text"
                  inputMode="numeric"
                />
              </div>
            </div>
          ))}
        </div>
      </fieldset>
    </div>
  )
}
