'use client'

import { cn } from '@/lib/utils'
import { forwardRef } from 'react'

type Props = {
  id: string
  className?: string
} & Omit<React.SelectHTMLAttributes<HTMLSelectElement>, 'className' | 'id'>

export const GovukSelect = forwardRef<HTMLSelectElement, Props>(
  function GovukSelect(
    { id, className, children, 'aria-invalid': ariaInvalid, ...rest },
    ref
  ) {
    const hasError = ariaInvalid === true || ariaInvalid === 'true'
    return (
      <select
        {...rest}
        ref={ref}
        id={id}
        aria-invalid={ariaInvalid}
        className={cn(
          'govuk-select',
          hasError && 'govuk-select--error',
          className
        )}
      >
        {children}
      </select>
    )
  }
)
