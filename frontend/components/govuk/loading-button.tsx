'use client'

import { GovukButton } from './button'

// Extract only the button variant (no href) to avoid anchor/button event handler conflicts
type Props = Omit<
  React.ComponentProps<typeof GovukButton>,
  'disabled'
> & {
  /** Disables the button and swaps its label while an async op is in flight. */
  isSubmitting?: boolean
  /** Label shown while `isSubmitting` is true. Defaults to `'Saving…'`. */
  loadingText?: string
}

/** GovukButton that disables itself and shows a loading label while `isSubmitting` is true. */
export function GovukLoadingButton({
  isSubmitting = false,
  loadingText = 'Saving…',
  children,
  ...rest
}: Props) {
  return (
    <GovukButton {...rest} disabled={isSubmitting}>
      {isSubmitting ? loadingText : children}
    </GovukButton>
  )
}
