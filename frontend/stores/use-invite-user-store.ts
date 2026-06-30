import { create } from 'zustand'

type InviteUserState = {
  name: string
  email: string
  setInviteDetails: (name: string, email: string) => void
  clearInviteDetails: () => void
}

export const useInviteUserStore = create<InviteUserState>((set) => ({
  name: '',
  email: '',
  setInviteDetails: (name, email) => set({ name, email }),
  clearInviteDetails: () => set({ name: '', email: '' }),
}))
