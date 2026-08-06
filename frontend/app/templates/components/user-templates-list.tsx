'use client'

import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import {
  GovukButton,
  GovukButtonLink,
  GovukHeading,
  GovukTable,
  GovukTableBody,
  GovukTableCell,
  GovukTableHead,
  GovukTableHeaderCell,
  GovukTableRow,
} from '@/components/govuk'
import { TemplateResponse } from '@/lib/client'
import {
  deleteUserTemplateUserTemplatesTemplateIdDeleteMutation,
  duplicateUserTemplateUserTemplatesTemplateIdDuplicatePostMutation,
  getUserTemplatesUserTemplatesGetOptions,
  getUserTemplatesUserTemplatesGetQueryKey,
} from '@/lib/client/@tanstack/react-query.gen'
import { useBannerStore } from '@/stores/use-banner-store'
import * as AlertDialogPrimitive from '@radix-ui/react-alert-dialog'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { FileSpreadsheet, FileType, FileWarning, Loader2 } from 'lucide-react'
import Link from 'next/link'
import posthog from 'posthog-js'
import { useMemo } from 'react'

export const UserTemplatesList = () => {
  const {
    data: templates = [],
    isLoading,
    isError,
  } = useQuery(getUserTemplatesUserTemplatesGetOptions())

  const sortedTemplates = [...templates].sort((a, b) => a.name.localeCompare(b.name))

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
      <GovukHeading size="m" as="h2" className="govuk-!-margin-top-4 govuk-!-margin-bottom-1">
        Your templates
      </GovukHeading>
      <p className="govuk-body govuk-!-margin-bottom-4">
        Includes common templates and any templates you create yourself.
      </p>

      <GovukTable>
        <GovukTableHead>
          <GovukTableRow>
            <GovukTableHeaderCell scope="col">Title</GovukTableHeaderCell>
            <GovukTableHeaderCell scope="col">
              Last updated
            </GovukTableHeaderCell>
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
              <GovukTableCell isNumeric>  
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

const TemplateCard = ({ template }: { template: TemplateResponse }) => {
  const setBanner = useBannerStore((store) => store.setBanner)
  const queryClient = useQueryClient()
  const deleteMutation = useMutation({
    ...deleteUserTemplateUserTemplatesTemplateIdDeleteMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: getUserTemplatesUserTemplatesGetQueryKey(),
      })
      setBanner({
        variant: 'important',
        title: 'Template deleted',
        message: `'${template.name}' deleted`,
      })
      posthog.capture('template_deleted')
    },
  })
  const duplicationMutation = useMutation({
    ...duplicateUserTemplateUserTemplatesTemplateIdDuplicatePostMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: getUserTemplatesUserTemplatesGetQueryKey(),
      })
      setBanner({
        variant: 'success',
        title: 'Success',
        message: `'${template.name} (Copy)' created`,
      })
      posthog.capture('template_duplicated')
    },
  })
  return (
    <div className="flex flex-col gap-4 rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
      <div>
        <h3 className="govuk-heading-s govuk-!-margin-bottom-1">
          {template.type === 'document' ? (
            <FileType className="govuk-!-display-inline govuk-!-margin-right-2 h-5 w-5 align-middle text-gray-500" />
          ) : (
            <FileSpreadsheet className="govuk-!-display-inline govuk-!-margin-right-2 h-5 w-5 align-middle text-gray-500" />
          )}
          {template.name}
        </h3>
        <p className="govuk-hint govuk-!-font-size-14 govuk-!-margin-bottom-0">
          {template.updated_datetime
            ? `Updated ${new Date(template.updated_datetime).toLocaleDateString()}`
            : 'Not yet updated'}
        </p>
      </div>
      <div className="govuk-body govuk-!-font-size-16 flex-1 text-gray-700">
        {template.description}
      </div>
      <div className="govuk-!-margin-top-2 flex flex-wrap gap-2">
        <GovukButtonLink
          href={`/templates/${template.id}`}
          variant="secondary"
          className="govuk-!-margin-bottom-0"
        >
          Edit template
        </GovukButtonLink>

        <GovukButton
          type="button"
          variant="secondary"
          className="govuk-!-margin-bottom-0"
          onClick={() => {
            duplicationMutation.mutate({
              path: { template_id: template.id! },
            })
          }}
          disabled={duplicationMutation.isPending}
        >
          Make a copy
        </GovukButton>
        <DeleteConfirmDialog
          template={template}
          onConfirm={() => {
            deleteMutation.mutate({
              path: { template_id: template.id! },
            })
          }}
          isDeleting={deleteMutation.isPending}
        />
      </div>
    </div>
  )
}

const DeleteConfirmDialog = ({
  template,
  onConfirm,
  isDeleting,
}: {
  template: TemplateResponse
  onConfirm: () => void
  isDeleting: boolean
}) => (
  <AlertDialog>
    <AlertDialogTrigger asChild>
      <GovukButton
        type="button"
        variant="warning"
        className="govuk-!-margin-bottom-0"
        disabled={isDeleting}
      >
        Delete
      </GovukButton>
    </AlertDialogTrigger>
    <AlertDialogContent>
      <AlertDialogHeader>
        <AlertDialogTitle className="govuk-heading-m govuk-!-margin-bottom-3">
          Delete Template
        </AlertDialogTitle>
        <p className="govuk-body">
          Are you sure you want to delete &quot;{template.name}
          &quot;? This action cannot be undone.
        </p>
      </AlertDialogHeader>
      <AlertDialogFooter className="govuk-!-margin-top-4 flex justify-end gap-2">
        <AlertDialogPrimitive.Cancel asChild>
          <GovukButton
            type="button"
            variant="secondary"
            className="govuk-!-margin-bottom-0"
          >
            Cancel
          </GovukButton>
        </AlertDialogPrimitive.Cancel>
        <AlertDialogPrimitive.Action asChild onClick={onConfirm}>
          <GovukButton
            type="button"
            variant="warning"
            className="govuk-!-margin-bottom-0"
          >
            Delete
          </GovukButton>
        </AlertDialogPrimitive.Action>
      </AlertDialogFooter>
    </AlertDialogContent>
  </AlertDialog>
)
