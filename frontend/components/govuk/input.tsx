'use client'

import { cn } from '@/lib/utils'
import { forwardRef } from 'react'

type Props = {
  id: string
  className?: string
} & Omit<React.InputHTMLAttributes<HTMLInputElement>, 'className' | 'id'>

export const GovukInput = forwardRef<HTMLInputElement, Props>(
  function GovukInput(
    { id, className, 'aria-invalid': ariaInvalid, ...rest },
    ref
  ) {
    const hasError = ariaInvalid === true || ariaInvalid === 'true'
    return (
      <input
        {...rest}
        ref={ref}
        id={id}
        aria-invalid={ariaInvalid}
        className={cn(
          'govuk-input',
          hasError && 'govuk-input--error',
          className
        )}
      />
    )
  }
)
