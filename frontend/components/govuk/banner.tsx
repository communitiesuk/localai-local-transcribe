import React from 'react'
import { cn } from '@/lib/utils'

type Props = {
  title: string
  variant?: 'default' | 'success'
  children: React.ReactNode
  className?: string
  titleId?: string
} & Omit<React.HTMLAttributes<HTMLDivElement>, 'className' | 'children'>

export function GovukNotificationBanner({
  title,
  variant = 'default',
  children,
  className,
  titleId = 'govuk-notification-banner-title',
  ...rest
}: Props) {
  return (
    <div
      className={cn(
        'govuk-notification-banner',
        variant === 'success' && 'govuk-notification-banner--success',
        className
      )}
      role={variant === 'success' ? 'alert' : 'region'}
      aria-labelledby={titleId}
      data-module="govuk-notification-banner"
      {...rest}
    >
      <div className="govuk-notification-banner__header flex justify-between">
        <h2 className="govuk-notification-banner__title" id={titleId}>
          {title}
        </h2>
      </div>

      <div className="govuk-notification-banner__content">{children}</div>
    </div>
  )
}
