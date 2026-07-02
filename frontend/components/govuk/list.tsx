import React from 'react'
import { cn } from '@/lib/utils'

type Props = {
  type?: 'unordered' | 'ordered'
  spaced?: boolean
  className?: string
  children: React.ReactNode
} & Omit<React.HTMLAttributes<HTMLElement>, 'className' | 'children'>

export function GovukList({
  type,
  spaced,
  className,
  children,
  ...rest
}: Props) {
  const listClassName = cn(
    'govuk-list',
    type && `govuk-list--${type}`,
    spaced && 'govuk-list--spaced',
    className
  )

  if (type === 'ordered') {
    return (
      <ol className={listClassName} {...rest}>
        {children}
      </ol>
    )
  }

  return (
    <ul className={listClassName} {...rest}>
      {children}
    </ul>
  )
}

export function GovukListItem({
  children,
  ...rest
}: React.LiHTMLAttributes<HTMLLIElement>) {
  return <li {...rest}>{children}</li>
}
