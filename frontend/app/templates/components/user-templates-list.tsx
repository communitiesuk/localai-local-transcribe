'use client'

import {
  getUserTemplatesUserTemplatesGetOptions,
} from '@/lib/client/@tanstack/react-query.gen'
import {
  GovukHeading,
  GovukTable,
  GovukTableBody,
  GovukTableCell,
  GovukTableHead,
  GovukTableHeaderCell,
  GovukTableRow,
} from '@/components/govuk'
import { useQuery } from '@tanstack/react-query'
import { FileWarning, Loader2 } from 'lucide-react'
import Link from 'next/link'
import { useMemo } from 'react'

export const UserTemplatesList = () => {
  const {
    data: templates = [],
    isLoading,
    isError,
  } = useQuery(getUserTemplatesUserTemplatesGetOptions())

  const sortedTemplates = useMemo(
    () => [...templates].sort((a, b) => a.name.localeCompare(b.name)),
    [templates]
  )

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
      <GovukHeading size="m" as="h2" className="govuk-!-margin-bottom-1">
        Your templates
      </GovukHeading>
      <p className="govuk-body govuk-!-margin-bottom-4">
        Includes common templates and any templates you create yourself.
      </p>

      <GovukTable>
        <GovukTableHead>
          <GovukTableRow>
            <GovukTableHeaderCell scope="col">Title</GovukTableHeaderCell>
            <GovukTableHeaderCell scope="col">Last updated</GovukTableHeaderCell>
            <GovukTableHeaderCell scope="col">
              <span className="govuk-visually-hidden">Actions</span>
            </GovukTableHeaderCell>
          </GovukTableRow>
        </GovukTableHead>
        <GovukTableBody>
          {sortedTemplates.map((template) => (
            <GovukTableRow key={template.id}>
              <GovukTableCell>{template.name}</GovukTableCell>
              <GovukTableCell>
                {template.updated_datetime
                  ? new Date(template.updated_datetime).toLocaleDateString(
                      'en-GB',
                      { day: '2-digit', month: '2-digit', year: 'numeric' }
                    )
                  : 'Original template'}
              </GovukTableCell>
              <GovukTableCell className="govuk-table__cell--numeric">
                <Link href={`/templates/${template.id}`} className="govuk-link">
                  Edit
                </Link>
              </GovukTableCell>
            </GovukTableRow>
          ))}
        </GovukTableBody>
      </GovukTable>
    </div>
  )
}
