import { TemplateData } from '@/types/templates'
import { create } from 'zustand'

type TemplateDraft = {
  templateId: string
  data: TemplateData
}

type TemplateDraftState = {
  draft: TemplateDraft | null
  titleConflict: boolean
  setDraft: (draft: TemplateDraft) => void
  setTitleConflict: (titleConflict: boolean) => void
  clearDraft: () => void
  handleRouteChange: (pathname: string) => void
}

export const useTemplateDraftStore = create<TemplateDraftState>((set, get) => ({
  draft: null,
  titleConflict: false,
  setDraft: (draft) => set({ draft }),
  setTitleConflict: (titleConflict) => set({ titleConflict }),
  clearDraft: () => set({ draft: null, titleConflict: false }),
  handleRouteChange: (pathname) => {
    const { draft, clearDraft } = get()

    if (!draft) {
      return
    }

    const editorPath = `/templates/${draft.templateId}`

    if (pathname === editorPath || pathname.startsWith(`${editorPath}/`)) {
      return
    }

    clearDraft()
  },
}))
