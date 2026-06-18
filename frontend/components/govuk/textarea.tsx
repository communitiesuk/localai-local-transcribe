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
  function GovukTextarea({ id, name, rows = 5, className, ...rest }, ref) {
    return (
      <textarea
        {...rest}
        ref={ref}
        id={id}
        name={name}
        rows={rows}
        className={cn('govuk-textarea', className)}
      />
    )
  }
)
