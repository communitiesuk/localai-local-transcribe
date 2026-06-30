'use client'

import { cn } from '@/lib/utils'

type Props = {
  summary: React.ReactNode
  className?: string
  children: React.ReactNode
} & Omit<
  React.DetailsHTMLAttributes<HTMLDetailsElement>,
  'className' | 'children'
>

export function GovukDetails({ summary, className, children, ...rest }: Props) {
  return (
    <details
      {...rest}
      className={cn('govuk-details', className)}
      data-module="govuk-details"
    >
      <summary className="govuk-details__summary">
        <span className="govuk-details__summary-text">{summary}</span>
      </summary>
      <div className="govuk-details__text">{children}</div>
    </details>
  )
}
