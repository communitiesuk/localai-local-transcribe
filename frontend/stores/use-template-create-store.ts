import { TemplateData } from '@/types/templates'
import { create } from 'zustand'

type TemplateCreateState = {
  draft: TemplateData | null
  titleConflict: boolean
  setDraft: (draft: TemplateData) => void
  setTitleConflict: (titleConflict: boolean) => void
  clear: () => void
}

export const useTemplateCreateStore = create<TemplateCreateState>((set) => ({
  draft: null,
  titleConflict: false,
  setDraft: (draft) => set({ draft }),
  setTitleConflict: (titleConflict) => set({ titleConflict }),
  clear: () => set({ draft: null, titleConflict: false }),
}))
