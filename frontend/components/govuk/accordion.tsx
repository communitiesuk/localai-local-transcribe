'use client'

import { cn } from '@/lib/utils'
import React from 'react'
import { useEffect, useRef } from 'react'

type AccordionProps = {
  id: string
  className?: string
  children: React.ReactNode
} & Omit<React.HTMLAttributes<HTMLDivElement>, 'className' | 'children' | 'id'>

type SectionProps = {
  heading: React.ReactNode
  headingLevel?: 2 | 3 | 4 | 5 | 6
  className?: string
  children: React.ReactNode
  _accordionId?: string
  _index?: number
}

const headingTag = {
  2: 'h2',
  3: 'h3',
  4: 'h4',
  5: 'h5',
  6: 'h6',
} as const

function Section({
  heading,
  headingLevel = 2,
  className,
  children,
  _accordionId,
  _index,
}: SectionProps) {
  const Heading = headingTag[headingLevel]
  const headingId = _accordionId
    ? `${_accordionId}-heading-${_index}`
    : undefined
  const contentId = _accordionId
    ? `${_accordionId}-content-${_index}`
    : undefined

  return (
    <div className={cn('govuk-accordion__section', className)}>
      <div className="govuk-accordion__section-header">
        <Heading className="govuk-accordion__section-heading">
          <span className="govuk-accordion__section-button" id={headingId}>
            {heading}
          </span>
        </Heading>
      </div>
      <div className="govuk-accordion__section-content" id={contentId}>
        {children}
      </div>
    </div>
  )
}

function GovukAccordionBase({
  id,
  className,
  children,
  ...rest
}: AccordionProps) {
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

  const injected = React.Children.map(children, (child, index) =>
    React.isValidElement(child)
      ? React.cloneElement(child as React.ReactElement<SectionProps>, {
          _accordionId: id,
          _index: index + 1,
        })
      : child
  )

  return (
    <div ref={wrappedRef}>
      <div
        {...rest}
        id={id}
        className={cn('govuk-accordion', className)}
        data-module="govuk-accordion"
      >
        {injected}
      </div>
    </div>
  )
}

GovukAccordionBase.Section = Section

export const GovukAccordion = GovukAccordionBase
export const GovukAccordionSection = Section
