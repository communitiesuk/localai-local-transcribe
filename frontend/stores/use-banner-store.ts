import { create } from 'zustand'

type Banner = {
  variant: 'important' | 'success'
  title: string
  message: string
}

type BannerState = {
  banner: Banner | null
  setBanner: (banner: Banner) => void
  clearBanner: () => void
}

export const useBannerStore = create<BannerState>((set) => ({
  banner: null,
  setBanner: (banner) => set({ banner }),
  clearBanner: () => set({ banner: null }),
}))
