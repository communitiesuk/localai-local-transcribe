import { cn } from '@/lib/utils'

type Props = {
  size?: 's' | 'm' | 'l' | 'xl'
  className?: string
  children: React.ReactNode
} & Omit<React.HTMLAttributes<HTMLLegendElement>, 'className' | 'children'>

export function GovukLegend({ size, className, children, ...rest }: Props) {
  return (
    <legend
      {...rest}
      className={cn(
        'govuk-fieldset__legend',
        size && `govuk-fieldset__legend--${size}`,
        className
      )}
    >
      {children}
    </legend>
  )
}
