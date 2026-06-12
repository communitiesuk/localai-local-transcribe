import { cn } from '@/lib/utils'

type Props = {
  hasError?: boolean
  className?: string
  children: React.ReactNode
} & Omit<React.HTMLAttributes<HTMLDivElement>, 'className' | 'children'>

export function GovukFormGroup({
  hasError,
  className,
  children,
  ...rest
}: Props) {
  return (
    <div
      {...rest}
      className={cn(
        'govuk-form-group',
        hasError && 'govuk-form-group--error',
        className
      )}
    >
      {children}
    </div>
  )
}
