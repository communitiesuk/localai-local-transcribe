import {
  hrefWithParams,
  recordingSearchQueryFromSearchParams,
  setRecordingSearchParams,
  valuesFromRecordingSearchParams,
} from '@/components/recent-meetings/search-recording-params'
import { SearchRecordingsFormData } from '@/types/search-recordings'
import { describe, expect, it } from 'vitest'

const searchValues: SearchRecordingsFormData = {
  dateOfRecording: { day: '9', month: '7', year: '' },
  clientName: ' Jane Smith ',
  caseId: ' CASE-123 ',
  subject: ' Assessment ',
  clientDateOfBirth: { day: '12', month: '4', year: '1985' },
}

describe('recording search params', () => {
  it('sets search params while preserving unrelated params for the caller', () => {
    const params = new URLSearchParams('sort=oldest&page=3')

    setRecordingSearchParams(params, searchValues)

    expect(params.get('sort')).toBe('oldest')
    expect(params.get('page')).toBe('3')
    expect(params.get('date_of_recording_day')).toBe('9')
    expect(params.get('date_of_recording_month')).toBe('7')
    expect(params.has('date_of_recording')).toBe(false)
    expect(params.get('client_name')).toBe('Jane Smith')
    expect(params.get('case_id')).toBe('CASE-123')
    expect(params.get('subject')).toBe('Assessment')
    expect(params.get('client_date_of_birth')).toBe('1985-04-12')
  })

  it('hydrates form values from partial recording date params and full date params', () => {
    const params = new URLSearchParams(
      'date_of_recording_month=7&client_date_of_birth=1985-04-12&client_name=Jane'
    )

    expect(valuesFromRecordingSearchParams(params)).toEqual({
      dateOfRecording: { day: '', month: '7', year: '' },
      clientName: 'Jane',
      caseId: '',
      subject: '',
      clientDateOfBirth: { day: '12', month: '04', year: '1985' },
    })
  })

  it('builds backend query params for partial recording date but not partial DOB', () => {
    const params = new URLSearchParams(
      'date_of_recording_day=9&date_of_recording_month=7&client_date_of_birth_month=4&client_name=Jane'
    )

    expect(recordingSearchQueryFromSearchParams(params)).toEqual({
      date_of_recording: undefined,
      date_of_recording_day: 9,
      date_of_recording_month: 7,
      date_of_recording_year: undefined,
      client_name: 'Jane',
      case_id: undefined,
      subject: undefined,
      client_date_of_birth: undefined,
    })
  })

  it('builds full date query params when all date parts are present', () => {
    const params = new URLSearchParams(
      'date_of_recording_day=9&date_of_recording_month=7&date_of_recording_year=2026&client_date_of_birth_day=12&client_date_of_birth_month=4&client_date_of_birth_year=1985'
    )

    expect(recordingSearchQueryFromSearchParams(params)).toEqual({
      date_of_recording: '2026-07-09',
      date_of_recording_day: 9,
      date_of_recording_month: 7,
      date_of_recording_year: 2026,
      client_name: undefined,
      case_id: undefined,
      subject: undefined,
      client_date_of_birth: '1985-04-12',
    })
  })

  it('formats hrefs without leaving a trailing question mark', () => {
    expect(hrefWithParams('/transcriptions', new URLSearchParams())).toBe(
      '/transcriptions'
    )
    expect(
      hrefWithParams('/transcriptions', new URLSearchParams('sort=oldest'))
    ).toBe('/transcriptions?sort=oldest')
  })
})
