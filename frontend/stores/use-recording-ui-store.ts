import { create } from 'zustand'

type RecordingStates = 'idle' | 'recording' | 'paused' | 'review'

type RecordingUiStore = {
  recordingState: RecordingStates
  setRecordingState: (state: RecordingStates) => void
  resetRecordingUi: () => void
}

export const useRecordingUiStore = create<RecordingUiStore>((set) => ({
  recordingState: 'idle',
  setRecordingState: (recordingState) => set({ recordingState }),
  resetRecordingUi: () => set({ recordingState: 'idle' }),
}))
