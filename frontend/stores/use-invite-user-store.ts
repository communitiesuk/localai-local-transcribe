import { create } from 'zustand'

type InviteUserState = {
  name: string
  email: string
  organisationId?: string
  setInviteDetails: (
    name: string,
    email: string,
    organisationId?: string
  ) => void
  clearInviteDetails: () => void
}

export const useInviteUserStore = create<InviteUserState>((set) => ({
  name: '',
  email: '',
  organisationId: '',
  setInviteDetails: (name, email, organisationId) =>
    set({ name, email, organisationId }),
  clearInviteDetails: () => set({ name: '', email: '', organisationId: '' }),
}))
