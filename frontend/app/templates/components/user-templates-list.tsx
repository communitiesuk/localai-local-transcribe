'use client'

import { ExampleTemplatesDialog } from '@/app/templates/components/example-templates-dialog'
import {
  exampleDocumentTemplates,
  exampleFormTemplates,
} from '@/app/templates/data/example-templates'
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import * as AlertDialogPrimitive from '@radix-ui/react-alert-dialog'
import { GovukButton, GovukButtonLink } from '@/components/govuk'
import { TemplateResponse } from '@/lib/client'
import {
  deleteUserTemplateUserTemplatesTemplateIdDeleteMutation,
  duplicateUserTemplateUserTemplatesTemplateIdDuplicatePostMutation,
  getUserTemplatesUserTemplatesGetOptions,
  getUserTemplatesUserTemplatesGetQueryKey,
} from '@/lib/client/@tanstack/react-query.gen'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Copy,
  Edit,
  FileSpreadsheet,
  FileType,
  FileWarning,
  Loader2,
  Trash2,
} from 'lucide-react'
import { useRouter } from 'next/navigation'
import posthog from 'posthog-js'
import { useMemo } from 'react'

export const UserTemplatesList = () => {
  const {
    data: templates = [],
    isLoading,
    isError,
  } = useQuery(getUserTemplatesUserTemplatesGetOptions())
  const [documentTemplates, formTemplates] = useMemo(() => {
    const docs = []
    const forms = []
    for (const template of templates) {
      if (template.type == 'document') {
        docs.push(template)
      } else {
        forms.push(template)
      }
    }
    return [docs, forms]
  }, [templates])
  const router = useRouter()
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
      <div className="govuk-!-margin-bottom-4">
        <div className="flex items-center gap-4">
          <h3 className="govuk-heading-m govuk-!-margin-bottom-0 flex items-center gap-2">
            <FileType className="h-6 w-6 text-gray-700" />
            Document
          </h3>
        </div>
        <p className="govuk-body govuk-hint govuk-!-margin-top-1">
          Customise the structure and style of your minutes.
        </p>
      </div>
      <div className="govuk-!-margin-bottom-8 grid auto-rows-fr gap-4 md:grid-cols-2 lg:grid-cols-3">
        <div className="flex flex-col justify-center gap-4 rounded-lg border border-dashed border-gray-300 bg-gray-50 p-4 shadow-sm">
          <GovukButtonLink
            href="/templates/new?type=document"
            isStartButton
            variant="secondary"
            className="govuk-!-margin-bottom-0 flex items-center justify-center"
          >
            Create a new template
          </GovukButtonLink>
          <ExampleTemplatesDialog
            onSelectTemplate={(example) => {
              router.push(`/templates/new?example=${example.name}`)
            }}
            examples={exampleDocumentTemplates}
          />
        </div>
        {documentTemplates.map((template) => (
          <TemplateCard template={template} key={template.id} />
        ))}
      </div>
      <div className="govuk-!-margin-bottom-4">
        <div className="flex items-center gap-4">
          <h3 className="govuk-heading-m govuk-!-margin-bottom-0 flex items-center gap-2">
            <FileSpreadsheet className="h-6 w-6 text-gray-700" /> Form
          </h3>
        </div>
        <p className="govuk-body govuk-hint govuk-!-margin-top-1">
          For complex summarisation of meetings into many questions and answers.
        </p>
      </div>
      <div className="grid auto-rows-fr gap-4 md:grid-cols-2 lg:grid-cols-3">
        <div className="flex flex-col justify-center gap-4 rounded-lg border border-dashed border-gray-300 bg-gray-50 p-4 shadow-sm">
          <GovukButtonLink
            href="/templates/new?type=form"
            isStartButton
            variant="secondary"
            className="govuk-!-margin-bottom-0 flex items-center justify-center"
          >
            Create a new template
          </GovukButtonLink>
          <ExampleTemplatesDialog
            onSelectTemplate={(example) => {
              router.push(`/templates/new?example=${example.name}`)
            }}
            examples={exampleFormTemplates}
          />
        </div>
        {formTemplates.map((template) => (
          <TemplateCard template={template} key={template.id} />
        ))}
      </div>
    </div>
  )
}
const TemplateCard = ({ template }: { template: TemplateResponse }) => {
  const queryClient = useQueryClient()
  const deleteMutation = useMutation({
    ...deleteUserTemplateUserTemplatesTemplateIdDeleteMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: getUserTemplatesUserTemplatesGetQueryKey(),
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
      posthog.capture('template_duplicated')
    },
  })
  return (
    <div className="flex flex-col gap-4 rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
      <div>
        <h4 className="govuk-heading-s govuk-!-margin-bottom-1 flex items-center gap-2">
          {template.type === 'document' ? (
            <FileType className="h-5 w-5 text-gray-500" />
          ) : (
            <FileSpreadsheet className="h-5 w-5 text-gray-500" />
          )}
          {template.name}
        </h4>
        <p className="govuk-hint govuk-!-font-size-14 govuk-!-margin-bottom-0">
          Updated {new Date(template.updated_datetime!).toLocaleDateString()}
        </p>
      </div>
      <div className="govuk-body govuk-!-font-size-16 flex-1 text-gray-700">
        {template.description}
      </div>
      <div className="govuk-!-margin-top-2 flex flex-wrap gap-2">
        <GovukButtonLink
          href={`/templates/${template.id}`}
          variant="secondary"
          className="govuk-!-margin-bottom-0 flex items-center gap-2"
        >
          <Edit size={14} />
          Edit template
        </GovukButtonLink>

        <GovukButton
          type="button"
          variant="secondary"
          className="govuk-!-margin-bottom-0 flex items-center gap-2"
          onClick={() => {
            duplicationMutation.mutate({
              path: { template_id: template.id },
            })
          }}
          disabled={duplicationMutation.isPending}
        >
          {duplicationMutation.isPending ? (
            <Loader2 className="animate-spin" size={14} />
          ) : (
            <Copy size={14} />
          )}
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
        className="govuk-!-margin-bottom-0 flex items-center gap-2"
        disabled={isDeleting}
      >
        {isDeleting ? (
          <Loader2 className="animate-spin" size={14} />
        ) : (
          <Trash2 size={14} />
        )}
        Delete
      </GovukButton>
    </AlertDialogTrigger>
    <AlertDialogContent>
      <AlertDialogHeader>
        <h2 className="govuk-heading-m govuk-!-margin-bottom-3">
          Delete Template
        </h2>
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
