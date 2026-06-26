import { create } from 'zustand'

type BannerState = {
  message: string | null
  setBanner: (message: string) => void
  clearBanner: () => void
}

export const useBannerStore = create<BannerState>((set) => ({
  message: null,
  setBanner: (message: string) => set({ message }),
  clearBanner: () => set({ message: null }),
}))
