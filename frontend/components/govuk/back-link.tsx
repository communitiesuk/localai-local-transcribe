import { cn } from '@/lib/utils'

type Props = {
  href: string
  inverse?: boolean
  className?: string
  children?: React.ReactNode
} & Omit<
  React.AnchorHTMLAttributes<HTMLAnchorElement>,
  'href' | 'className' | 'children'
>

export function GovukBackLink({
  href,
  inverse,
  className,
  children,
  ...rest
}: Props) {
  return (
    <a
      {...rest}
      href={href}
      className={cn(
        'govuk-back-link',
        inverse && 'govuk-back-link--inverse',
        className
      )}
    >
      {children ?? 'Back'}
    </a>
  )
}
