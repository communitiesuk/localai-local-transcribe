const recordingDetailsErrorMessageMappings = [
  {
    prefix: 'The date recorded must include',
    text: 'Recording date must include a day, month, year, hour and minute',
  },
  {
    prefix: 'The date recorded must be between',
    text: 'The recording date cannot be in the future',
  },
  {
    prefix: 'The date recorded must be today or in the past',
    text: 'The recording date and time cannot be in the future',
  },
  {
    prefix: 'The date recorded must be a real date',
    text: 'Recording date must be a real date',
  },
  {
    prefix: 'The date recorded must be a real time',
    text: 'Recording time must be a real time',
  },
  {
    prefix: "The client's date of birth must include",
    text: 'Date of birth must include a day, month and year',
  },
  {
    prefix: "The client's date of birth must be between",
    text: 'Date of birth must be a real date',
  },
  {
    prefix: "The client's date of birth must be today or in the past",
    text: 'Date of birth must be a real date',
  },
  {
    prefix: "The client's date of birth must be a real date",
    text: 'Date of birth must be a real date',
  },
]

export const recordingDetailsErrorSummaryText = (message: string): string =>
  recordingDetailsErrorMessageMappings.find(({ prefix }) =>
    message.startsWith(prefix)
  )?.text ?? message
