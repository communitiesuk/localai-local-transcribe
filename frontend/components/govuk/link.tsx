import { cn } from '@/lib/utils'

type Props = {
  href: string
  className?: string
  children: React.ReactNode
} & Omit<
  React.AnchorHTMLAttributes<HTMLAnchorElement>,
  'className' | 'children' | 'href'
>

export function GovukLink({ href, className, children, ...rest }: Props) {
  return (
    <a {...rest} href={href} className={cn('govuk-link', className)}>
      {children}
    </a>
  )
}
