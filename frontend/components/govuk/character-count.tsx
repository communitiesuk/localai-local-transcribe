'use client'

import { cn } from '@/lib/utils'
import React, { useEffect, useRef } from 'react'

type Props = {
  /**
   * Id of the textarea this count belongs to. govuk-frontend looks for a
   * message element with the id `${id}-info`, so the textarea must also list
   * `${id}-info` in its aria-describedby.
   */
  id: string
  /** Maximum number of characters allowed. */
  maxLength: number
  className?: string
  /** The form group containing the label, hint and textarea. */
  children: React.ReactNode
}

/**
 * GOV.UK Character count. Wraps a form group whose textarea carries the
 * `govuk-js-character-count` class, and renders the count message that
 * govuk-frontend turns into a live "You have X characters remaining" region.
 *
 * The count does not stop the user typing past the limit, which is the
 * canonical GOV.UK behaviour; it turns red and the form rejects on submit.
 */
export function GovukCharacterCount({
  id,
  maxLength,
  className,
  children,
}: Props) {
  const wrappedRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    let cancelled = false
    import('govuk-frontend')
      .then(({ initAll }) => {
        if (!cancelled && wrappedRef.current) {
          initAll(wrappedRef.current)
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
    <div ref={wrappedRef}>
      <div
        className={cn('govuk-character-count', className)}
        data-module="govuk-character-count"
        data-maxlength={maxLength}
      >
        {children}
        <div
          id={`${id}-info`}
          className="govuk-hint govuk-character-count__message"
        >
          You can enter up to {maxLength} characters
        </div>
      </div>
    </div>
  )
}
