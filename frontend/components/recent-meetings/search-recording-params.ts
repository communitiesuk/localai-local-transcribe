import { SearchRecordingsFormData } from '@/types/search-recordings'

type SearchParamsReader = {
  get: (key: string) => string | null
}

export const recordingSearchParamKeys = [
  'date_of_recording_day',
  'date_of_recording_month',
  'date_of_recording_year',
  'date_of_recording',
  'client_name',
  'case_id',
  'subject',
  'client_date_of_birth_day',
  'client_date_of_birth_month',
  'client_date_of_birth_year',
  'client_date_of_birth',
]

const defaultDate = { day: '', month: '', year: '' }

const datePartsFromSearchParams = (
  searchParams: SearchParamsReader,
  prefix: string
) => {
  const day = searchParams.get(`${prefix}_day`)
  const month = searchParams.get(`${prefix}_month`)
  const year = searchParams.get(`${prefix}_year`)

  if (day || month || year) {
    return {
      day: day ?? '',
      month: month ?? '',
      year: year ?? '',
    }
  }

  const date = searchParams.get(prefix)
  if (!date) {
    return defaultDate
  }

  const [yearPart, monthPart, dayPart] = date.split('-')
  return {
    day: dayPart ?? '',
    month: monthPart ?? '',
    year: yearPart ?? '',
  }
}

const dateQueryFromParts = ({
  day,
  month,
  year,
}: {
  day: string
  month: string
  year: string
}) => {
  const trimmedDay = day.trim()
  const trimmedMonth = month.trim()
  const trimmedYear = year.trim()

  if (!trimmedDay || !trimmedMonth || !trimmedYear) {
    return undefined
  }

  return `${trimmedYear.padStart(4, '0')}-${trimmedMonth.padStart(
    2,
    '0'
  )}-${trimmedDay.padStart(2, '0')}`
}

const textQueryFromSearchParams = (
  searchParams: SearchParamsReader,
  key: string
) => searchParams.get(key)?.trim() || undefined

const datePartQueryNumber = (value: string, max?: number) => {
  const trimmedValue = value.trim()

  if (!/^\d+$/.test(trimmedValue)) {
    return undefined
  }

  const numberValue = Number(trimmedValue)

  if (numberValue < 1 || (max !== undefined && numberValue > max)) {
    return undefined
  }

  return numberValue
}

const datePartQueryFromParts = (parts: {
  day: string
  month: string
  year: string
}) => ({
  day: datePartQueryNumber(parts.day, 31),
  month: datePartQueryNumber(parts.month, 12),
  year: datePartQueryNumber(parts.year),
})

export const valuesFromRecordingSearchParams = (
  searchParams: SearchParamsReader
): SearchRecordingsFormData => ({
  dateOfRecording: datePartsFromSearchParams(searchParams, 'date_of_recording'),
  clientName: searchParams.get('client_name') ?? '',
  caseId: searchParams.get('case_id') ?? '',
  subject: searchParams.get('subject') ?? '',
  clientDateOfBirth: datePartsFromSearchParams(
    searchParams,
    'client_date_of_birth'
  ),
})

export const recordingSearchQueryFromSearchParams = (
  searchParams: SearchParamsReader
) => {
  const dateOfRecordingParts = datePartsFromSearchParams(
    searchParams,
    'date_of_recording'
  )
  const clientDateOfBirthParts = datePartsFromSearchParams(
    searchParams,
    'client_date_of_birth'
  )
  const dateOfRecording = datePartQueryFromParts(dateOfRecordingParts)

  return {
    date_of_recording: dateQueryFromParts(dateOfRecordingParts) ?? undefined,
    date_of_recording_day: dateOfRecording.day,
    date_of_recording_month: dateOfRecording.month,
    date_of_recording_year: dateOfRecording.year,
    client_name: textQueryFromSearchParams(searchParams, 'client_name'),
    case_id: textQueryFromSearchParams(searchParams, 'case_id'),
    subject: textQueryFromSearchParams(searchParams, 'subject'),
    client_date_of_birth:
      dateQueryFromParts(clientDateOfBirthParts) ?? undefined,
  }
}

export const setRecordingSearchParams = (
  params: URLSearchParams,
  values: SearchRecordingsFormData
) => {
  setOrDelete(params, 'date_of_recording_day', values.dateOfRecording.day)
  setOrDelete(params, 'date_of_recording_month', values.dateOfRecording.month)
  setOrDelete(params, 'date_of_recording_year', values.dateOfRecording.year)
  setOrDelete(params, 'client_name', values.clientName)
  setOrDelete(params, 'case_id', values.caseId)
  setOrDelete(params, 'subject', values.subject)
  setOrDelete(params, 'client_date_of_birth_day', values.clientDateOfBirth.day)
  setOrDelete(
    params,
    'client_date_of_birth_month',
    values.clientDateOfBirth.month
  )
  setOrDelete(
    params,
    'client_date_of_birth_year',
    values.clientDateOfBirth.year
  )

  const dateOfRecording = dateQueryFromParts(values.dateOfRecording)
  const clientDateOfBirth = dateQueryFromParts(values.clientDateOfBirth)

  if (dateOfRecording) {
    params.set('date_of_recording', dateOfRecording)
  } else {
    params.delete('date_of_recording')
  }

  if (clientDateOfBirth) {
    params.set('client_date_of_birth', clientDateOfBirth)
  } else {
    params.delete('client_date_of_birth')
  }
}

export const hrefWithParams = (pathname: string, params: URLSearchParams) => {
  const queryString = params.toString()
  return queryString ? `${pathname}?${queryString}` : pathname
}

const setOrDelete = (params: URLSearchParams, key: string, value: string) => {
  const trimmedValue = value.trim()
  if (trimmedValue) {
    params.set(key, trimmedValue)
  } else {
    params.delete(key)
  }
}
