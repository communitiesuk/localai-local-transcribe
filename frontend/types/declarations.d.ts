// Included to fix type issue in audio-player.tsx
// To support older browsers we support the case where webkitAudioContext is used instead of AudioContext
// Typescript doesn't include webkitAudioContext in it's type definition for Window.
// So here we add it.
declare interface Window {
  webkitAudioContext: typeof AudioContext
}

// govuk-frontend v6.1 ships no .d.ts files. Declare the runtime entry point used by GovukInit.
declare module 'govuk-frontend' {
  export function initAll(scope?: Element | Document): void
}
