'use client'

import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { listUnlabelledTranscriptionsTranscriptionsUnlabelledGetOptions } from '@/lib/client/@tanstack/react-query.gen'
import { recordingSearchQueryFromSearchParams } from '@/components/recent-meetings/search-recording-params'
import { GovukHeading, GovukHint } from '@/components/govuk'
import {
  GovukTable,
  GovukTableBody,
  GovukTableCell,
  GovukTableHead,
  GovukTableHeaderCell,
  GovukTableRow,
} from '@/components/govuk/table'
import Link from 'next/link'
import { useSearchParams } from 'next/navigation'

export const UnlabelledTranscriptions = () => {
  const searchParams = useSearchParams()
  const sort = searchParams.get('sort') === 'oldest' ? 'oldest' : 'newest'
  const searchQuery = recordingSearchQueryFromSearchParams(searchParams)
  const {
    data: response,
    isLoading,
    error,
  } = useQuery({
    ...listUnlabelledTranscriptionsTranscriptionsUnlabelledGetOptions({
      query: { sort, ...searchQuery },
    }),
    placeholderData: keepPreviousData,
  })

  const transcriptions = response?.items || []
  const totalCount = response?.total_count || 0

  return (
    <div>
      <GovukHeading as="h2" size="m">
        Unlabelled recordings
      </GovukHeading>
      <GovukHint className="govuk-!-margin-bottom-0">
        Total: {totalCount}
      </GovukHint>
      {isLoading ? (
        <div className="flex items-center justify-center py-8">
          <div className="text-gray-500">Loading recordings...</div>
        </div>
      ) : error ? (
        <div className="flex items-center justify-center py-8">
          <div className="text-red-500">
            Error loading unlabelled recordings
          </div>
        </div>
      ) : transcriptions.length === 0 ? (
        <div className="flex items-center justify-center py-8">
          <div className="text-gray-500">No unlabelled recordings found</div>
        </div>
      ) : (
        <>
          <GovukTable>
            <GovukTableHead>
              <GovukTableRow>
                <GovukTableHeaderCell className="govuk-!-padding-1 govuk-!-width-one-quarter">
                  <span className={'govuk-visually-hidden'}>Date recorded</span>
                </GovukTableHeaderCell>
                <GovukTableHeaderCell className="govuk-!-padding-1">
                  <span className={'govuk-visually-hidden'}>Date recorded</span>
                </GovukTableHeaderCell>
                <GovukTableHeaderCell className="govuk-!-padding-1">
                  <span className={'govuk-visually-hidden'}>
                    Link to recording
                  </span>
                </GovukTableHeaderCell>
              </GovukTableRow>
            </GovukTableHead>
            <GovukTableBody>
              {transcriptions.map((transcription) => (
                <GovukTableRow key={transcription.id}>
                  <GovukTableCell>Date recorded</GovukTableCell>
                  <GovukTableCell>
                    {transcription.date_of_recording ? (
                      <div>
                        {new Date(
                          transcription.date_of_recording
                        ).toLocaleDateString()}
                        <br />
                        {new Date(
                          transcription.date_of_recording
                        ).toLocaleTimeString()}
                      </div>
                    ) : null}
                  </GovukTableCell>
                  <GovukTableCell className="govuk-!-text-align-right">
                    <Link
                      className="govuk-link"
                      href={`/transcriptions/${transcription.id}`}
                    >
                      View
                    </Link>
                  </GovukTableCell>
                </GovukTableRow>
              ))}
            </GovukTableBody>
          </GovukTable>
        </>
      )}
    </div>
  )
}
