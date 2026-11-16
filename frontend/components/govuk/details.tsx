'use client'

import { cn } from '@/lib/utils'

type Props = {
  summary: React.ReactNode
  className?: string
  open?: boolean
  children: React.ReactNode
} & Omit<
  React.DetailsHTMLAttributes<HTMLDetailsElement>,
  'className' | 'children'
>

export const GovukDetails = ({
  summary,
  className,
  children,
  open,
  ...rest
}: Props) => {
  return (
    <details
      {...rest}
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
