'use client'

import {
  GovukHeading,
  GovukTable,
  GovukTableBody,
  GovukTableCell,
  GovukTableHead,
  GovukTableHeaderCell,
  GovukTableRow,
} from '@/components/govuk'
import { useTemplates } from '@/hooks/use-templates'
import type { SelectableTemplate } from '@/hooks/use-templates'
import { FileWarning, Loader2 } from 'lucide-react'
import Link from 'next/link'
import type { ReactNode } from 'react'

export const UserTemplatesList = () => {
  const { sortedDefaultTemplates, sortedUserTemplates, isLoading, isError } =
    useTemplates()

  if (isLoading) {
    return <Loader2 className="animate-spin" />
  }

  if (isError) {
    return (
      <div className="govuk-body flex items-center gap-2 text-red-600">
        <FileWarning />
        <span>Something went wrong fetching your templates</span>
      </div>
    )
  }

  return (
    <div>
      <TemplateTable
        title="Standard templates"
        description="Includes common templates for your department. You cannot delete these - duplicate one if you want to customise it."
        templates={sortedDefaultTemplates}
        action={(template) => (
          <Link
            href={`/templates/default/${encodeURIComponent(template.name)}/duplicate`}
            className="govuk-link"
          >
            Duplicate
          </Link>
        )}
      />

      <GovukHeading
        size="m"
        as="h2"
        className="govuk-!-margin-top-6 govuk-!-margin-bottom-1"
      >
        Your templates
      </GovukHeading>
      <p className="govuk-body govuk-!-margin-bottom-4">
        The templates you create yourself (including duplicates of standard
        templates).
      </p>

      <TemplateTable
        templates={sortedUserTemplates}
        showUpdatedDate
        emptyMessage="You haven't made any templates yet."
        action={(template) =>
          hasEditableTemplateId(template) ? (
            <Link href={`/templates/${template.id}`} className="govuk-link">
              Edit
            </Link>
          ) : null
        }
      />
    </div>
  )
}

const hasEditableTemplateId = (
  template: SelectableTemplate
): template is SelectableTemplate & { id: string } => template.id !== null

const TemplateTable = ({
  title,
  description,
  templates,
  showUpdatedDate = false,
  emptyMessage,
  action,
}: {
  title?: string
  description?: string
  templates: SelectableTemplate[]
  showUpdatedDate?: boolean
  emptyMessage?: string
  action?: (template: SelectableTemplate) => ReactNode
}) => (
  <section>
    {title && (
      <GovukHeading
        size="m"
        as="h2"
        className="govuk-!-margin-top-0 govuk-!-margin-bottom-1"
      >
        {title}
      </GovukHeading>
    )}
    {description && (
      <p className="govuk-body govuk-!-margin-bottom-4">{description}</p>
    )}
    {templates.length ? (
      <GovukTable>
        <GovukTableHead>
          <GovukTableRow>
            <GovukTableHeaderCell scope="col">Title</GovukTableHeaderCell>
            {showUpdatedDate && (
              <GovukTableHeaderCell scope="col">
                Last updated
              </GovukTableHeaderCell>
            )}
            {action && (
              <GovukTableHeaderCell scope="col">
                <span className="govuk-visually-hidden">Actions</span>
              </GovukTableHeaderCell>
            )}
          </GovukTableRow>
        </GovukTableHead>
        <GovukTableBody>
          {templates.map((template) => (
            <GovukTableRow key={template.id ?? `default-${template.name}`}>
              <GovukTableCell>{template.name}</GovukTableCell>
              {showUpdatedDate && (
                <GovukTableCell>
                  {template.updated_datetime
                    ? new Date(template.updated_datetime).toLocaleDateString(
                        'en-GB',
                        { day: '2-digit', month: '2-digit', year: 'numeric' }
                      )
                    : ''}
                </GovukTableCell>
              )}
              {action && (
                <GovukTableCell isNumeric>{action(template)}</GovukTableCell>
              )}
            </GovukTableRow>
          ))}
        </GovukTableBody>
      </GovukTable>
    ) : (
      emptyMessage && <p className="govuk-body">{emptyMessage}</p>
    )}
  </section>
)
