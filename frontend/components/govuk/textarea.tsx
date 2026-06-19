'use client'

import { cn } from '@/lib/utils'
import { forwardRef } from 'react'

type Props = {
  id: string
  name?: string
  rows?: number
  className?: string
} & Omit<
  React.TextareaHTMLAttributes<HTMLTextAreaElement>,
  'className' | 'rows' | 'id'
>

export const GovukTextarea = forwardRef<HTMLTextAreaElement, Props>(
  function GovukTextarea({ id, name, rows = 5, className, 'aria-invalid': ariaInvalid, ...rest }, ref) {
    const hasError = ariaInvalid === true || ariaInvalid === 'true'
    
    return (
      <textarea
        {...rest}
        ref={ref}
        id={id}
        name={name}
        rows={rows}
        aria-invalid={ariaInvalid}
        className={cn(
          'govuk-textarea',
          hasError && 'govuk-textarea--error',
          className
        )}
      />
    )
  }
)