'use client'

import { GovukHint } from '@/components/govuk/hint'
import { cn } from '@/lib/utils'
import React, { useEffect, useRef } from 'react'

type Props = {
  /** Textarea id. Its aria-describedby must include `${id}-info`. */
  id: string
  maxLength: number
  hasError?: boolean
  className?: string
  /** Label, hint and textarea. The textarea needs `govuk-js-character-count`. */
  children: React.ReactNode
} & Omit<React.HTMLAttributes<HTMLDivElement>, 'className' | 'children' | 'id'>

// Renders the form group itself, as GDS puts both classes on one element.
export function GovukCharacterCount({
  id,
  maxLength,
  hasError,
  className,
  children,
  ...rest
}: Props) {
  const rootRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    let cancelled = false
    import('govuk-frontend')
      .then(({ CharacterCount }) => {
        if (cancelled || !rootRef.current) return
        try {
          new CharacterCount(rootRef.current)
        } catch {
          // Already initialised, e.g. the double effect run in React strict mode.
        }
      })
      .catch((error) => {
        console.error('Error loading govuk-frontend:', error)
      })
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <div
      {...rest}
      ref={rootRef}
      className={cn(
        'govuk-form-group govuk-character-count',
        hasError && 'govuk-form-group--error',
        className
      )}
      data-module="govuk-character-count"
      data-maxlength={maxLength}
    >
      {children}
      <GovukHint id={`${id}-info`} className="govuk-character-count__message">
        You can enter up to {maxLength} characters
      </GovukHint>
    </div>
  )
}
