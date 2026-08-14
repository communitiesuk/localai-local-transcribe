import { create } from 'zustand'

type BannerLink = {
  href: string
  text: string
}

type Banner = {
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
