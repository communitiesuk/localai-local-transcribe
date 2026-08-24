import { cn } from '@/lib/utils'

type SectionBreakSize = 'xl' | 'l' | 'm'

type Props = {
  size?: SectionBreakSize
  visible?: boolean
  className?: string
} & Omit<React.HTMLAttributes<HTMLHRElement>, 'className' | 'children'>

export function GovukSectionBreak({
  size,
  visible = true,
  className,
  ...rest
}: Props) {
  return (
    <hr
      {...rest}
      className={cn(
        'govuk-section-break',
        size && `govuk-section-break--${size}`,
        visible && 'govuk-section-break--visible',
        className
      )}
    />
  )
}
