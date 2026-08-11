'use client'

import { GovukButton, GovukButtonGroup } from '@/components/govuk'
import { useTemplateDraftStore } from '@/stores/use-template-draft-store'
import { TemplateData } from '@/types/templates'
import { useRouter } from 'next/navigation'
import { useFormContext } from 'react-hook-form'

// Usage note: `goToSave` receives the validated data and should be wired into
// the form's `onSubmit` so that saving is gated by validation; the others fire
// regardless of validity.
export function useTemplateInterstitialActions(templateId: string) {
  const router = useRouter()
  const form = useFormContext<TemplateData>()
  const setDraft = useTemplateDraftStore((store) => store.setDraft)

  const snapshotAndGo = (segment: string) => {
    setDraft({ templateId, data: form.getValues() })
    router.push(`/templates/${templateId}/${segment}`)
  }

  return {
    goToSave: (data: TemplateData) => {
      setDraft({ templateId, data })
      router.push(`/templates/${templateId}/save`)
    },
    goToDuplicate: () => snapshotAndGo('duplicate'),
    goToDelete: () => snapshotAndGo('delete'),
    goToCancel: () => snapshotAndGo('cancel'),
  }
}

export function TemplateEditorActions({ templateId }: { templateId: string }) {
  const { goToDuplicate, goToDelete, goToCancel } =
    useTemplateInterstitialActions(templateId)

  return (
    <div>
      <hr className="govuk-section-break govuk-section-break--visible govuk-!-margin-bottom-6" />
      <GovukButtonGroup>
        <GovukButton type="submit" className="govuk-!-margin-bottom-0">
          Save template
        </GovukButton>
        <GovukButton
          type="button"
          variant="secondary"
          className="govuk-!-margin-bottom-0"
          onClick={goToDuplicate}
        >
          Duplicate template
        </GovukButton>
        <GovukButton
          type="button"
          variant="warning"
          className="govuk-!-margin-bottom-0"
          onClick={goToDelete}
        >
          Delete template
        </GovukButton>
        <GovukButton variant="link" onClick={goToCancel}>
          Cancel
        </GovukButton>
      </GovukButtonGroup>
    </div>
  )
}
