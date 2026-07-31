'use client'

import {
  getUserTemplatesUserTemplatesGetOptions,
  getUserTemplatesUserTemplatesGetQueryKey,
} from '@/lib/client/@tanstack/react-query.gen'
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
    [templates],
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
      <h2 className="govuk-heading-m govuk-!-margin-bottom-1">
        Your templates
      </h2>
      <p className="govuk-body govuk-!-margin-bottom-4">
        Includes common templates and any templates you create yourself.
      </p>

      <table className="govuk-table">
        <thead className="govuk-table__head">
          <tr className="govuk-table__row">
            <th className="govuk-table__header" scope="col">
              Title
            </th>
            <th className="govuk-table__header" scope="col">
              Last updated
            </th>
            <th className="govuk-table__header" scope="col">
              <span className="govuk-visually-hidden">Actions</span>
            </th>
          </tr>
        </thead>
        <tbody className="govuk-table__body">
          {sortedTemplates.map((template) => (
            <tr className="govuk-table__row" key={template.id}>
              <td className="govuk-table__cell">{template.name}</td>
              <td className="govuk-table__cell">
                {template.updated_datetime
                  ? new Date(template.updated_datetime).toLocaleDateString(
                      'en-GB',
                      { day: '2-digit', month: '2-digit', year: 'numeric' },
                    )
                  : 'Original template'}
              </td>
              <td className="govuk-table__cell govuk-table__cell--numeric">
                <Link
                  href={`/templates/${template.id}`}
                  className="govuk-link"
                >
                  Edit
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
