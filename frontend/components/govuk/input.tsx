import { cn } from '@/lib/utils'

type Props = {
  className?: string
} & Omit<React.InputHTMLAttributes<HTMLInputElement>, 'className'>

export function GovukInput({ className, ...rest }: Props) {
  return <input {...rest} className={cn('govuk-input', className)} />
}
