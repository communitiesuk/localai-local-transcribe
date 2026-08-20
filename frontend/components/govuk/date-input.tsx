'use client'

import { cn } from '@/lib/utils'
import React from 'react'
import { FieldValues, useController, UseControllerProps } from 'react-hook-form'
import { GovukInput } from '@/components/govuk/input'
import { GovukFormGroup } from '@/components/govuk/form-group'

type DateValue = {
  day: string
  month: string
  year: string
}

type DateInputProps<T extends FieldValues> = {
  id: string
  legend: React.ReactNode
  hint?: React.ReactNode
  className?: string
  mustBePastOrFuture?: 'past' | 'future'
  description?: string
} & Omit<React.HTMLAttributes<HTMLDivElement>, 'className' | 'id'> &
  UseControllerProps<T>

const items = [
  { name: 'day', label: 'Day', width: 'govuk-input--width-2' },
  { name: 'month', label: 'Month', width: 'govuk-input--width-2' },
  { name: 'year', label: 'Year', width: 'govuk-input--width-4' },
] as const

function dateIsReal(date: DateValue): boolean {
  const { day, month, year } = date

  if (![day, month, year].every((s) => /^\d+$/.test(s))) return false

  const d = Number(day)
  const m = Number(month)
  const y = Number(year)

  if (m < 1 || m > 12) return false

  const daysInMonth = new Date(y, m, 0).getDate() // day 0 of next month = last day of this one
  return d >= 1 && d <= daysInMonth
}

export function validateDateEntry(
  value: DateValue,
  pastOrFuture?: 'past' | 'future',
  description: string = 'date'
): { message: string; fields: ('day' | 'month' | 'year')[] } | null {
  const missingFields = Object.entries(value)
    .filter(([_, v]) => !v)
    .map(([field, _]) => field) as ('day' | 'month' | 'year')[]

  if (missingFields.length === 3) {
    return null
  }

  if (missingFields.length > 0) {
    return {
      message:
        `The ${description} must include a ` +
        new Intl.ListFormat('en').format(missingFields),
      fields: missingFields,
    }
  }

  if (!dateIsReal(value)) {
    return {
      message: `The ${description} must be a real date`,
      fields: ['day', 'month', 'year'],
    }
  }

  const date = new Date(
    Number(value.year),
    Number(value.month) - 1,
    Number(value.day)
  )
  const today = new Date()
  today.setHours(0, 0, 0, 0) // ignore time

  if (date > today && pastOrFuture === 'past') {
    return {
      message: `The ${description} must be in the past`,
      fields: ['day', 'month', 'year'],
    }
  } else if (date < today && pastOrFuture === 'future') {
    return {
      message: `The ${description} must be in the future`,
      fields: ['day', 'month', 'year'],
    }
  }
  return null
}

export function GovukDateInput<T extends FieldValues>({
  id,
  name,
  legend,
  hint,
  className,
  control,
  mustBePastOrFuture,
  description = 'date',
  ...rest
}: DateInputProps<T>) {
  const { field, fieldState } = useController({
    name,
    control,
  })

  const value = (field.value as DateValue) || { day: '', month: '', year: '' }

  const hintId = hint ? `${id}-hint` : undefined

  const validationResult = validateDateEntry(
    value,
    mustBePastOrFuture,
    description
  )
  const hasError = !!fieldState.error || !!validationResult

  return (
    <GovukFormGroup className={className} hasError={hasError}>
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
        {hasError && (
          <p id="date-input-error" className="govuk-error-message">
            <span className="govuk-visually-hidden">Error:</span>{' '}
            {fieldState.error?.message || validationResult?.message}
          </p>
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
                <GovukInput
                  className={cn('govuk-date-input__input', item.width)}
                  id={`${id}-${item.name}`}
                  name={`${id}-${item.name}`}
                  type="text"
                  inputMode="numeric"
                  value={value[item.name]}
                  onChange={(e) => {
                    field.onChange({
                      ...field.value,
                      [item.name]: e.target.value,
                    })
                  }}
                  aria-invalid={
                    validationResult?.fields.includes(item.name)
                      ? 'true'
                      : undefined
                  }
                />
              </div>
            </div>
          ))}
        </div>
      </fieldset>
    </GovukFormGroup>
  )
}
