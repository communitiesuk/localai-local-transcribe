import { create } from 'zustand'

type NewOrg = {
  name: string
  allowedDomains: string[]
}

type NewOrgState = {
  newOrg: NewOrg | null
  setNewOrg: (newOrg: NewOrg) => void
  clearNewOrg: () => void
}

export const useNewOrgStore = create<NewOrgState>((set) => ({
  newOrg: null,
  setNewOrg: (newOrg) => set({ newOrg }),
  clearNewOrg: () => set({ newOrg: null }),
}))
