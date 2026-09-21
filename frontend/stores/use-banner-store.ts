import { create } from 'zustand'

export type BannerLink = {
  href: string
  text: string
}

export type Banner = {
  variant: 'important' | 'success'
  title: string
  message: string
  link?: BannerLink
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
