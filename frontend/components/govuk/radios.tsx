'use client'

import { cn } from '@/lib/utils'
import { Fragment, forwardRef } from 'react'
import { GovukLabel } from './label'

// A single option for the `options` prop; `hint` is optional.
export type RadioOption = {
  label: React.ReactNode
  value: string
  hint?: React.ReactNode
  conditional?: React.ReactNode
}

type RadiosProps = {
  name: string
  value?: string
  onChange?: (value: string) => void
  disabled?: boolean
  className?: string
  options: RadioOption[]
} & Omit<React.HTMLAttributes<HTMLDivElement>, 'className' | 'onChange'>

export const GovukRadios = forwardRef<HTMLDivElement, RadiosProps>(
  function GovukRadios(
    { name, value, onChange, disabled, className, options, ...rest },
    ref
  ) {
    return (
      <div {...rest} ref={ref} className={cn('govuk-radios', className)}>
        {options.map((option, index) => {
          // Canonical GDS ids: first item → `${name}`, rest → `${name}-2`, …
          const resolvedId = index === 0 ? name : `${name}-${index + 1}`
          const hintId = `${resolvedId}-hint`
          const conditionalId = `${resolvedId}-conditional`

          return (
            <Fragment key={option.value}>
              <div className="govuk-radios__item">
                <input
                  className="govuk-radios__input"
                  id={resolvedId}
                  name={name}
                  type="radio"
                  value={option.value}
                  checked={value === option.value}
                  onChange={(event) => {
                    if (event.target.checked) {
                      onChange?.(option.value)
                    }
                  }}
                  disabled={disabled}
                  aria-describedby={option.hint ? hintId : undefined}
                  aria-controls={option.conditional ? conditionalId : undefined}
                />
                <GovukLabel
                  className="govuk-radios__label"
                  htmlFor={resolvedId}
                >
                  {option.label}
                </GovukLabel>
                {option.hint && (
                  <div className="govuk-hint govuk-radios__hint" id={hintId}>
                    {option.hint}
                  </div>
                )}
              </div>
              {option.conditional && (
                <div
                  id={conditionalId}
                  className={cn(
                    'govuk-radios__conditional',
                    value !== option.value &&
                      'govuk-radios__conditional--hidden'
                  )}
                  hidden={value !== option.value}
                >
                  {option.conditional}
                </div>
              )}
            </Fragment>
          )
        })}
      </div>
    )
  }
)
