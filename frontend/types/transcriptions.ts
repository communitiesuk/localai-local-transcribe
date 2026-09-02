export type TranscriptionDetailsData = {
  dateOfRecording: {
    day: string
    month: string
    year: string
    hour: string
    minute: string
  }
  clientName: string
  caseId: string
  subject: string
  clientDateOfBirth: { day: string; month: string; year: string }
}
