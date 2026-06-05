import { cn } from '@/lib/utils'

type Props = {
  htmlFor?: string
  size?: 's' | 'm' | 'l' | 'xl'
  className?: string
  children: React.ReactNode
} & Omit<
  React.LabelHTMLAttributes<HTMLLabelElement>,
  'className' | 'children' | 'htmlFor'
>

export function GovukLabel({
  htmlFor,
  size,
  className,
  children,
  ...rest
}: Props) {
  return (
    <label
      {...rest}
      htmlFor={htmlFor}
      className={cn('govuk-label', size && `govuk-label--${size}`, className)}
    >
      {children}
    </label>
  )
}
