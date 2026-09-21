import { create } from 'zustand'

type InviteUserState = {
  name: string
  email: string
  evaluationId: string
  organisationId?: string
  setInviteDetails: (
    name: string,
    email: string,
    evaluationId: string,
    organisationId?: string
  ) => void
  clearInviteDetails: () => void
}

export const useInviteUserStore = create<InviteUserState>((set) => ({
  name: '',
  email: '',
  evaluationId: '',
  organisationId: '',
  setInviteDetails: (name, email, evaluationId, organisationId) =>
    set({ name, email, evaluationId, organisationId }),
  clearInviteDetails: () =>
    set({ name: '', email: '', evaluationId: '', organisationId: '' }),
}))
