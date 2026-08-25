'use client'

import { getUserTemplateUserTemplatesTemplateIdGetOptions } from '@/lib/client/@tanstack/react-query.gen'
import { useTemplateDraftStore } from '@/stores/use-template-draft-store'
import { useQuery } from '@tanstack/react-query'

// If a template is present in the draft store, then that name is used to avoid
// a fetch. Otherwise, falls back to fetching the template name via API.
function useTemplateName(templateId: string): string | undefined {
  const draft = useTemplateDraftStore((store) => store.draft)
  const draftName =
    draft?.templateId === templateId ? draft.data.name : undefined

  const { data: template } = useQuery({
    ...getUserTemplateUserTemplatesTemplateIdGetOptions({
      path: { template_id: templateId },
    }),
    enabled: draftName === undefined,
  })

  return draftName ?? template?.name
}

export default useTemplateName
