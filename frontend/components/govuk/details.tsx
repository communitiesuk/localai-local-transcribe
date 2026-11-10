'use client'

import { cn } from '@/lib/utils'
import { forwardRef } from 'react'

type Props = {
  summary: React.ReactNode
  className?: string
  open?: boolean
  children: React.ReactNode
} & Omit<
  React.DetailsHTMLAttributes<HTMLDetailsElement>,
  'className' | 'children'
>

export const GovukDetails = forwardRef<HTMLDetailsElement, Props>(
  function GovukDetails({ summary, className, children, open, ...rest }, ref) {
    return (
      <details
        {...rest}
        ref={ref}
        className={cn('govuk-details', className)}
        data-module="govuk-details"
        open={open === true || undefined}
        suppressHydrationWarning
      >
        <summary className="govuk-details__summary">
          <span className="govuk-details__summary-text">{summary}</span>
        </summary>
        <div className="govuk-details__text">{children}</div>
      </details>
    )
  }
)
