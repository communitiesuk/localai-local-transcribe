export type SearchRecordingsFormData = {
  dateOfRecording: { day: string; month: string; year: string }
  clientName: string
  caseId: string
  subject: string
  clientDateOfBirth: { day: string; month: string; year: string }
}
