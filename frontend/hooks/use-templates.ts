'use client'

import {
  getTemplatesTemplatesGetOptions,
  getUserTemplatesUserTemplatesGetOptions,
} from '@/lib/client/@tanstack/react-query.gen'
import type { AgendaUsage } from '@/lib/client'
import { useQuery } from '@tanstack/react-query'

export type SelectableTemplate = {
  id: string
  name: string
  description: string
  agenda_usage: AgendaUsage
  updated_datetime: string | null
}

const DEFAULT_TEMPLATE_ID_PREFIX = 'default-'

export const isDefaultTemplateId = (id: string | null) =>
  id?.startsWith(DEFAULT_TEMPLATE_ID_PREFIX) ?? false

export const userTemplateIdForRequest = (template: { id: string | null }) =>
  template.id === null || isDefaultTemplateId(template.id) ? null : template.id

export const templateValue = (template: { id: string | null; name: string }) =>
  template.id ?? ''

const sortTemplatesByName = (templates: SelectableTemplate[]) =>
  [...templates].sort((a, b) => a.name.localeCompare(b.name))

export const useTemplates = () => {
  const defaultTemplatesQuery = useQuery(getTemplatesTemplatesGetOptions())
  const userTemplatesQuery = useQuery(getUserTemplatesUserTemplatesGetOptions())

  const defaultTemplates: SelectableTemplate[] = (
    defaultTemplatesQuery.data ?? []
  ).map((template) => ({
    ...template,
    updated_datetime: null,
  }))
  const userTemplates: SelectableTemplate[] = (
    userTemplatesQuery.data ?? []
  ).map((template) => ({
    id: template.id,
    name: template.name,
    description: template.description,
    agenda_usage: 'not_used',
    updated_datetime: template.updated_datetime,
  }))
  const templates = [...defaultTemplates, ...userTemplates]

  return {
    sortedDefaultTemplates: sortTemplatesByName(defaultTemplates),
    sortedUserTemplates: sortTemplatesByName(userTemplates),
    sortedTemplates: sortTemplatesByName(templates),
    isLoading: defaultTemplatesQuery.isLoading || userTemplatesQuery.isLoading,
    isLoadingDefaultTemplates: defaultTemplatesQuery.isLoading,
    isLoadingUserTemplates: userTemplatesQuery.isLoading,
    isError: defaultTemplatesQuery.isError || userTemplatesQuery.isError,
    refetchTemplates: () => {
      void defaultTemplatesQuery.refetch()
      void userTemplatesQuery.refetch()
    },
  }
}
