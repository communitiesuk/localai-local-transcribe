'use client'

import { cn } from '@/lib/utils'
import { useRouter } from 'next/navigation'

type Props = {
  href?: string
  onClick?: React.MouseEventHandler<HTMLAnchorElement>
  inverse?: boolean
  className?: string
  children?: React.ReactNode
} & Omit<
  React.AnchorHTMLAttributes<HTMLAnchorElement>,
  'href' | 'className' | 'children' | 'onClick'
>

export function GovukBackLink({
  href,
  onClick,
  inverse,
  className,
  children,
  ...rest
}: Props) {
  const router = useRouter()

  const handleBack = (event: React.MouseEvent<HTMLAnchorElement>) => {
    if (onClick) {
      onClick(event)
    } else if (!href) {
      event.preventDefault()
      router.back()
    }
  }

  return (
    <a
      {...rest}
      href={href ?? '#'}
      className={cn(
        'govuk-back-link',
        inverse && 'govuk-back-link--inverse',
        className
      )}
      onClick={handleBack}
    >
      {children ?? 'Back'}
    </a>
  )
}
