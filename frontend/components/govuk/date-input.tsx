'use client'

import { cn } from '@/lib/utils'
import React, { useState } from 'react'
import { FieldValues, useController, UseControllerProps } from 'react-hook-form'
import { GovukInput } from '@/components/govuk/input'
import { GovukFormGroup } from '@/components/govuk/form-group'

type DateValue = {
  day: string
  month: string
  year: string
  hour?: string
  minute?: string
}

type DateField = 'day' | 'month' | 'year' | 'hour' | 'minute'

type DateValidationMode = 'full-date' | 'partial-date'

type DateInputProps<T extends FieldValues> = {
  id: string
  legend: React.ReactNode
  hint?: React.ReactNode
  className?: string
  mustBePastOrFuture?: 'past' | 'future'
  description?: string
  validationMode?: DateValidationMode
  required?: boolean
  /** Renders an "Hour" and "Minute" field alongside day/month/year, within the same fieldset. */
  includeTime?: boolean
} & Omit<React.HTMLAttributes<HTMLDivElement>, 'className' | 'id'> &
  UseControllerProps<T>

const dateItems = [
  { name: 'day', label: 'Day', width: 'govuk-input--width-2' },
  { name: 'month', label: 'Month', width: 'govuk-input--width-2' },
  { name: 'year', label: 'Year', width: 'govuk-input--width-4' },
] as const

const timeItems = [
  { name: 'hour', label: 'Hour', width: 'govuk-input--width-2' },
  { name: 'minute', label: 'Minute', width: 'govuk-input--width-2' },
] as const

const MIN_YEAR = 1920

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

function timeIsValid(value: DateValue): boolean {
  const hour = value.hour ?? ''
  const minute = value.minute ?? ''

  if (![hour, minute].every((s) => /^\d+$/.test(s))) return false

  const h = Number(hour)
  const m = Number(minute)
  return h >= 0 && h <= 23 && m >= 0 && m <= 59
}

export function validateDateEntry(
  value: DateValue | undefined,
  pastOrFuture?: 'past' | 'future',
  description: string = 'date',
  validationMode: DateValidationMode = 'full-date',
  required: boolean = false,
  includeTime: boolean = false
): { message: string; fields: DateField[] } | null {
  const fieldNames: DateField[] = includeTime
    ? ['day', 'month', 'year', 'hour', 'minute']
    : ['day', 'month', 'year']
  const emptyValue: DateValue = includeTime
    ? { day: '', month: '', year: '', hour: '', minute: '' }
    : { day: '', month: '', year: '' }
  const dateValue = { ...emptyValue, ...value }
  const missingFields = fieldNames.filter((field) => !dateValue[field])

  if (missingFields.length === fieldNames.length) {
    if (required) {
      return {
        message:
          `The ${description} must include a ` +
          new Intl.ListFormat('en').format(missingFields),
        fields: missingFields,
      }
    }
    return null
  }

  if (validationMode === 'partial-date') {
    const invalidFields = dateItems
      .filter(({ name }) => dateValue[name] && !/^\d+$/.test(dateValue[name]))
      .map(({ name }) => name)

    const day = Number(dateValue.day)
    const month = Number(dateValue.month)
    const year = Number(dateValue.year)

    if (dateValue.day && (day < 1 || day > 31)) {
      invalidFields.push('day')
    }
    if (dateValue.month && (month < 1 || month > 12)) {
      invalidFields.push('month')
    }
    if (dateValue.year && year < 1) {
      invalidFields.push('year')
    }

    if (invalidFields.length > 0) {
      return {
        message: `${description} must be a real date`,
        fields: invalidFields,
      }
    }

    const today = new Date()
    if (
      dateValue.year &&
      pastOrFuture === 'past' &&
      year > today.getFullYear()
    ) {
      return {
        message: `The ${description} cannot be in the future`,
        fields: ['year'],
      }
    }

    if (missingFields.length > 0) {
      return null
    }
  }

  if (missingFields.length > 0) {
    return {
      message:
        `The ${description} must include a ` +
        new Intl.ListFormat('en').format(missingFields),
      fields: missingFields,
    }
  }

  if (!dateIsReal(dateValue)) {
    return {
      message: `The ${description} must be a real date`,
      fields: ['day', 'month', 'year'],
    }
  }

  if (includeTime && !timeIsValid(dateValue)) {
    return {
      message: `The ${description} must be a real time`,
      fields: ['hour', 'minute'],
    }
  }

  const date = new Date(
    Number(dateValue.year),
    Number(dateValue.month) - 1,
    Number(dateValue.day),
    includeTime ? Number(dateValue.hour) : 0,
    includeTime ? Number(dateValue.minute) : 0
  )
  const today = new Date()
  if (!includeTime) {
    today.setHours(0, 0, 0, 0) // ignore time
  }
  const year = Number(dateValue.year)

  if (year < MIN_YEAR || year > today.getFullYear()) {
    return {
      message: `The ${description} must be between 1 January ${MIN_YEAR} and today`,
      fields: ['day', 'month', 'year'],
    }
  }

  if (date > today && pastOrFuture === 'past') {
    return {
      message: `The ${description} must be today or in the past`,
      fields: includeTime ? fieldNames : ['day', 'month', 'year'],
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
  validationMode = 'full-date',
  required = false,
  includeTime = false,
  rules,
  ...rest
}: DateInputProps<T>) {
  const [errorFields, setErrorFields] = useState<DateField[]>([])

  const { field, fieldState } = useController({
    name,
    control,
    rules: {
      ...rules,
      validate: (value: DateValue) => {
        const validationResult = validateDateEntry(
          value,
          mustBePastOrFuture,
          description,
          validationMode,
          required,
          includeTime
        )
        setErrorFields(validationResult?.fields ?? [])
        return validationResult ? validationResult.message : true
      },
    },
  })

  const emptyValue: DateValue = includeTime
    ? { day: '', month: '', year: '', hour: '', minute: '' }
    : { day: '', month: '', year: '' }
  const value = { ...emptyValue, ...(field.value as DateValue) }
  const items = includeTime ? [...dateItems, ...timeItems] : dateItems

  const hintId = hint ? `${id}-hint` : undefined

  const hasError = !!fieldState.error
  const errorId = hasError ? `${id}-error` : undefined

  return (
    <GovukFormGroup className={className} hasError={hasError}>
      <fieldset
        className="govuk-fieldset"
        role="group"
        aria-describedby={
          [hintId, errorId].filter((id) => id != undefined).join(' ') ||
          undefined
        }
      >
        <legend className="govuk-fieldset__legend">{legend}</legend>
        {hint && (
          <div id={hintId} className="govuk-hint">
            {hint}
          </div>
        )}
        {hasError && (
          <p id={errorId} className="govuk-error-message">
            <span className="govuk-visually-hidden">Error:</span>{' '}
            {fieldState.error?.message}
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
                    errorFields.includes(item.name) ? 'true' : undefined
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
