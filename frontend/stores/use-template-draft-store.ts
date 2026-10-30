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
}

export const useTemplateDraftStore = create<TemplateDraftState>((set) => ({
  draft: null,
  setDraft: (draft) => set({ draft }),
  clearDraft: () => set({ draft: null }),
}))
