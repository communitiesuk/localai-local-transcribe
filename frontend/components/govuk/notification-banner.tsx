import { cn } from '@/lib/utils'

type Variant = 'important' | 'success'

type Props = {
  variant?: Variant
  title?: string
  titleId?: string
  className?: string
  children: React.ReactNode
} & Omit<React.HTMLAttributes<HTMLDivElement>, 'className' | 'children' | 'role'>

const defaultTitles: Record<Variant, string> = {
  important: 'Important',
  success: 'Success',
}

export function GovukNotificationBanner({
  variant = 'important',
  title,
  titleId = 'govuk-notification-banner-title',
  className,
  children,
  ...rest
}: Props) {
  const isSuccess = variant === 'success'

  return (
    <div
      {...rest}
      className={cn(
        'govuk-notification-banner',
        isSuccess && 'govuk-notification-banner--success',
        className
      )}
      role={isSuccess ? 'alert' : 'region'}
      aria-labelledby={titleId}
      data-module="govuk-notification-banner"
    >
      <div className="govuk-notification-banner__header">
        <h2 className="govuk-notification-banner__title" id={titleId}>
          {title ?? defaultTitles[variant]}
        </h2>
      </div>
      <div className="govuk-notification-banner__content">{children}</div>
    </div>
  )
}
