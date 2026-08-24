import { create } from 'zustand'

export type RecordingState =
  | 'idle'
  | 'starting'
  | 'recording'
  | 'paused'
  | 'stopConfirm'
  | 'stopping'
  | 'stopped'

export type RecordingUIStore = {
  recordingUIState: RecordingState
  setRecordingUIState: (state: RecordingState) => void
  resetRecordingUI: () => void
}

export const useRecordingUIStore = create<RecordingUIStore>((set) => ({
  recordingUIState: 'idle',
  setRecordingUIState: (recordingUIState) => set({ recordingUIState }),
  resetRecordingUI: () => set({ recordingUIState: 'idle' }),
}))
