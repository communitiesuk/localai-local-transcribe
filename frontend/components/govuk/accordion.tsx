import { cn } from '@/lib/utils'

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
}

const headingTag = {
  2: 'h2',
  3: 'h3',
  4: 'h4',
  5: 'h5',
  6: 'h6',
} as const

function Section({ heading, headingLevel = 2, className, children }: SectionProps) {
  const Heading = headingTag[headingLevel]

  return (
    <div className={cn('govuk-accordion__section', className)}>
      <div className="govuk-accordion__section-header">
        <Heading className="govuk-accordion__section-heading">
          <span className="govuk-accordion__section-button">{heading}</span>
        </Heading>
      </div>
      <div className="govuk-accordion__section-content">{children}</div>
    </div>
  )
}

export function GovukAccordion({ id, className, children, ...rest }: AccordionProps) {
  return (
    <div
      {...rest}
      id={id}
      className={cn('govuk-accordion', className)}
      data-module="govuk-accordion"
    >
      {children}
    </div>
  )
}

GovukAccordion.Section = Section
