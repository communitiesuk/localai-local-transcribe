import { cn } from '@/lib/utils'

type PanelPadding = 0 | 2 | 4 | 6 | 8

type PanelProps = {
  padding?: PanelPadding
  border?: boolean
  className?: string
} & Omit<React.HTMLAttributes<HTMLDivElement>, 'className'>

function GovukPanel({
  padding = 4,
  border = true,
  className,
  ...rest
}: PanelProps) {
  return (
    <div
      {...rest}
      data-slot="govuk-panel"
      className={cn(
        'app-panel',
        `app-panel--padding-${padding}`,
        border && 'app-panel--border',
        className
      )}
    />
  )
}

function GovukPanelHeader({
  className,
  ...props
}: React.ComponentProps<'div'>) {
  return (
    <div data-slot="govuk-panel-header" className={cn(className)} {...props} />
  )
}

function GovukPanelTitle({ className, ...props }: React.ComponentProps<'h2'>) {
  return (
    <h2
      data-slot="govuk-panel-title"
      className={cn('govuk-heading-s govuk-!-margin-bottom-1', className)}
      {...props}
    />
  )
}

function GovukPanelDescription({
  className,
  ...props
}: React.ComponentProps<'p'>) {
  return (
    <p
      data-slot="govuk-panel-description"
      className={cn(
        'govuk-body-s govuk-hint govuk-!-margin-bottom-4',
        className
      )}
      {...props}
    />
  )
}

function GovukPanelContent({
  className,
  ...props
}: React.ComponentProps<'div'>) {
  return (
    <div data-slot="govuk-panel-content" className={cn(className)} {...props} />
  )
}

function GovukPanelFooter({
  className,
  ...props
}: React.ComponentProps<'div'>) {
  return (
    <div
      data-slot="govuk-panel-footer"
      className={cn('govuk-!-margin-top-4', className)}
      {...props}
    />
  )
}

export {
  GovukPanel,
  GovukPanelHeader,
  GovukPanelTitle,
  GovukPanelDescription,
  GovukPanelContent,
  GovukPanelFooter,
}
