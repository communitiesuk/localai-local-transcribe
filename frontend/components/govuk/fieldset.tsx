import { cn } from '@/lib/utils'

type Props = {
  className?: string
  children: React.ReactNode
} & Omit<
  React.FieldsetHTMLAttributes<HTMLFieldSetElement>,
  'className' | 'children'
>

export function GovukFieldset({ className, children, ...rest }: Props) {
  return (
    <fieldset {...rest} className={cn('govuk-fieldset', className)}>
      {children}
    </fieldset>
  )
}
