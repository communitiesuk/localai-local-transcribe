'use client'

import { cn } from '@/lib/utils'

type Props = {
  onClick: React.MouseEventHandler<HTMLAnchorElement>
  inverse?: boolean
  className?: string
  children?: React.ReactNode
} & Omit<
  React.AnchorHTMLAttributes<HTMLAnchorElement>,
  'href' | 'className' | 'children' | 'onClick'
>

export function GovukBackLinkClient({
  onClick,
  inverse,
  className,
  children,
  ...rest
}: Props) {
  return (
    <a
      {...rest}
      href="#"
      className={cn(
        'govuk-back-link',
        inverse && 'govuk-back-link--inverse',
        className
      )}
      onClick={(event) => {
        event.preventDefault()
        onClick(event)
      }}
    >
      {children ?? 'Back'}
    </a>
  )
}
