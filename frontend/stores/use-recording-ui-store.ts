import { create } from 'zustand'

export type RecordingState =
  'idle' | 'starting' | 'recording' | 'paused' | 'stopConfirm' | 'stopping'

export type RecordingUIStore = {
  recordingUIState: RecordingState
  stoppedAtLimit: boolean
  setRecordingUIState: (state: RecordingState) => void
  setStoppedAtLimit: (stoppedAtLimit: boolean) => void
  resetRecordingUI: () => void
}

export const useRecordingUIStore = create<RecordingUIStore>((set) => ({
  recordingUIState: 'idle',
  stoppedAtLimit: false,
  setRecordingUIState: (recordingUIState) => set({ recordingUIState }),
  setStoppedAtLimit: (stoppedAtLimit) => set({ stoppedAtLimit }),
  resetRecordingUI: () =>
    set({ recordingUIState: 'idle', stoppedAtLimit: false }),
}))
