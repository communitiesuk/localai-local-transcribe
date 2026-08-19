import { cn } from '@/lib/utils'

type BodySize = 'default' | 'l' | 's'

type Props = {
  size?: BodySize
  className?: string
  children: React.ReactNode
} & Omit<React.HTMLAttributes<HTMLParagraphElement>, 'className' | 'children'>

const bodyClasses: Record<BodySize, string> = {
  default: 'govuk-body',
  l: 'govuk-body-l',
  s: 'govuk-body-s',
}

export function GovukBody({
  size = 'default',
  className,
  children,
  ...rest
}: Props) {
  return (
    <p {...rest} className={cn(bodyClasses[size], className)}>
      {children}
    </p>
  )
}
