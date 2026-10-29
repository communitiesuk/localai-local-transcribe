import Link from 'next/link'
import { cn } from '@/lib/utils'

export function GovukCancelLink({
  href,
  className,
}: {
  href: string
  className?: string
}) {
  return (
    <Link
      href={href}
      className={cn('govuk-link govuk-link--no-visited-state', className)}
    >
      Cancel
    </Link>
  )
}
