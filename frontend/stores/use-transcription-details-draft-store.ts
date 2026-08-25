import { TranscriptionDetailsData } from '@/types/transcriptions'
import { create } from 'zustand'

type TranscriptionDetailsDraft = {
  transcriptionId: string
  data: TranscriptionDetailsData
  isOpen: boolean
}

type TranscriptionDetailsDraftState = {
  draft: TranscriptionDetailsDraft | null
  setDraft: (draft: TranscriptionDetailsDraft) => void
  clearDraft: () => void
}

export const useTranscriptionDetailsDraftStore =
  create<TranscriptionDetailsDraftState>((set) => ({
    draft: null,
    setDraft: (draft) => set({ draft }),
    clearDraft: () => set({ draft: null }),
  }))
