import { cn } from '@/lib/utils'

export type TagColour =
  | 'grey'
  | 'green'
  | 'turquoise'
  | 'blue'
  | 'light-blue'
  | 'purple'
  | 'pink'
  | 'red'
  | 'orange'
  | 'yellow'

type Props = {
  colour?: TagColour
  className?: string
  children: React.ReactNode
} & Omit<React.HTMLAttributes<HTMLElement>, 'className' | 'children'>

export function GovukTag({ colour, className, children, ...rest }: Props) {
  return (
    <strong
      {...rest}
      className={cn('govuk-tag', colour && `govuk-tag--${colour}`, className)}
    >
      {children}
    </strong>
  )
}
