import { TemplateData } from '@/types/templates'
import { create } from 'zustand'

type TemplateDraft = {
  templateId: string
  data: TemplateData
}

type TemplateDraftState = {
  draft: TemplateDraft | null
  setDraft: (draft: TemplateDraft) => void
  clearDraft: () => void
  handleRouteChange: (pathname: string) => void
}

export const useTemplateDraftStore = create<TemplateDraftState>((set, get) => ({
  draft: null,
  setDraft: (draft) => set({ draft }),
  clearDraft: () => set({ draft: null }),
  handleRouteChange: (pathname) => {
    const { draft } = get()

    if (!draft) {
      return
    }

    const editorPath = `/templates/${draft.templateId}`

    if (pathname === editorPath || pathname.startsWith(`${editorPath}/`)) {
      return
    }

    set({ draft: null })
  },
}))
