import { cn } from '@/lib/utils'

type Props = {
  describedBy?: string
  className?: string
  children: React.ReactNode
} & Omit<
  React.FieldsetHTMLAttributes<HTMLFieldSetElement>,
  'className' | 'children' | 'aria-describedby'
>

export function GovukFieldset({
  describedBy,
  className,
  children,
  ...rest
}: Props) {
  return (
    <fieldset
      {...rest}
      aria-describedby={describedBy}
      className={cn('govuk-fieldset', className)}
    >
      {children}
    </fieldset>
  )
}
