import { cn } from '@/lib/utils'

type Props = {
  id?: string
  className?: string
  children: React.ReactNode
} & Omit<React.HTMLAttributes<HTMLDivElement>, 'className' | 'children' | 'id'>

export function GovukHint({ id, className, children, ...rest }: Props) {
  return (
    <div {...rest} id={id} className={cn('govuk-hint', className)}>
      {children}
    </div>
  )
}
