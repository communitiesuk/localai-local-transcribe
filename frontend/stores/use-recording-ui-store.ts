import { create } from 'zustand'

export type RecordingState =
  'idle' | 'starting' | 'recording' | 'paused' | 'stopped'

export type RecordingUiStore = {
  recordingState: RecordingState
  setRecordingState: (state: RecordingState) => void
  resetRecordingUi: () => void
}

export const useRecordingUiStore = create<RecordingUiStore>((set) => ({
  recordingState: 'idle',
  setRecordingState: (recordingState) => set({ recordingState }),
  resetRecordingUi: () => set({ recordingState: 'idle' }),
}))
