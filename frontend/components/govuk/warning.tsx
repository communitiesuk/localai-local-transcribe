import React from 'react'
import { cn } from '@/lib/utils'

type Props = {
  children: React.ReactNode
  className?: string
} & Omit<React.HTMLAttributes<HTMLDivElement>, 'className' | 'children'>

export function GovukWarningText({ children, className, ...rest }: Props) {
  return (
    <div className={cn('govuk-warning-text', className)} {...rest}>
      <span className="govuk-warning-text__icon" aria-hidden="true">
        !
      </span>

      <strong className="govuk-warning-text__text">
        <span className="govuk-visually-hidden">Warning</span>
        {children}
      </strong>
    </div>
  )
}
