import { create } from 'zustand'

type InviteUserState = {
  name: string
  email: string
  evaluationId: string
  setInviteDetails: (name: string, email: string, evaluationId: string) => void
  clearInviteDetails: () => void
}

export const useInviteUserStore = create<InviteUserState>((set) => ({
  name: '',
  email: '',
  evaluationId: '',
  setInviteDetails: (name, email, evaluationId) =>
    set({ name, email, evaluationId }),
  clearInviteDetails: () => set({ name: '', email: '', evaluationId: '' }),
}))
