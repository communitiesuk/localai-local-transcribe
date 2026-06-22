import { cn } from '@/lib/utils'

type Props = {
  size?: 's' | 'm' | 'l' | 'xl'
  className?: string
  children: React.ReactNode
  as?: 'h1' | 'h2' | 'h3'
} & Omit<React.HTMLAttributes<HTMLHeadingElement>, 'className' | 'children'>

export function GovukHeading({
  size = 'l',
  className,
  as: Tag = 'h1',
  children,
  ...rest
}: Props) {
  return (
    <Tag {...rest} className={cn(`govuk-heading-${size}`, className)}>
      {children}
    </Tag>
  )
}
