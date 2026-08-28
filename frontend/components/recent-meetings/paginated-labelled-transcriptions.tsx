'use client'

import { listLabelledTranscriptionsTranscriptionsLabelledGetOptions } from '@/lib/client/@tanstack/react-query.gen'
import { keepPreviousData, useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { usePathname, useRouter, useSearchParams } from 'next/navigation'
import { GovukHeading, GovukHint } from '@/components/govuk'
import {
  GovukTable,
  GovukTableBody,
  GovukTableCell,
  GovukTableHead,
  GovukTableHeaderCell,
  GovukTableRow,
} from '@/components/govuk/table'
import { GovukPagination } from '@/components/govuk/pagination'
import {
  hrefWithParams,
  recordingSearchQueryFromSearchParams,
} from '@/components/recent-meetings/search-recording-params'

export const getPageNumbers = (
  currentPage: number,
  totalPages: number,
  maxPagesToShow = 5
) => {
  const pages = []
  let startPage = Math.max(1, currentPage - Math.floor(maxPagesToShow / 2))
  const endPage = Math.min(totalPages, startPage + maxPagesToShow - 1)

  if (endPage - startPage + 1 < maxPagesToShow) {
    startPage = Math.max(1, endPage - maxPagesToShow + 1)
  }

  for (let i = startPage; i <= endPage; i++) {
    pages.push(i)
  }
  return pages
}

export const PaginatedLabelledTranscriptions = () => {
  const pathname = usePathname()
  const searchParams = useSearchParams()
  const router = useRouter()
  const currentPage = Number(searchParams.get('page')) || 1
  const pageSize = 10
  const sort = searchParams.get('sort') === 'oldest' ? 'oldest' : 'newest'
  const searchQuery = recordingSearchQueryFromSearchParams(searchParams)
  const {
    data: paginatedResponse,
    isLoading,
    error,
  } = useQuery({
    ...listLabelledTranscriptionsTranscriptionsLabelledGetOptions({
      query: { page: currentPage, page_size: pageSize, sort, ...searchQuery },
    }),
    refetchInterval: (query) =>
      !!query.state.data &&
      query.state.data.items?.some((t) =>
        ['awaiting_start', 'in_progress'].includes(t.status)
      )
        ? 5000
        : false,
    placeholderData: keepPreviousData,
  })

  if (paginatedResponse && paginatedResponse.total_pages < currentPage) {
    const params = new URLSearchParams(searchParams)
    params.set('page', String(paginatedResponse.total_pages))
    router.replace(hrefWithParams(pathname, params))
  }
  const transcriptions = paginatedResponse?.items || []
  const totalPages = paginatedResponse?.total_pages || 1
  const totalCount = paginatedResponse?.total_count || 0

  const formatRecordedDate = (date: string | null | undefined) =>
    date ? (
      <div>
        {new Date(date).toLocaleDateString('en-GB')}
        <br />
        {new Date(date).toLocaleTimeString('en-GB')}
      </div>
    ) : (
      '—'
    )

  return (
    <div>
      <GovukHeading as="h2" size="m">
        Labelled recordings
      </GovukHeading>
      <GovukHint>Total: {totalCount}</GovukHint>
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
          <div className="text-gray-500">No recordings to display</div>
        </div>
      ) : (
        <>
          <GovukTable>
            <GovukTableHead>
              <GovukTableRow>
                <GovukTableHeaderCell>Name</GovukTableHeaderCell>
                <GovukTableHeaderCell className="text-nowrap">
                  Case ID
                </GovukTableHeaderCell>
                <GovukTableHeaderCell className="govuk-!-width-one-third">
                  Subject
                </GovukTableHeaderCell>
                <GovukTableHeaderCell className="text-nowrap">
                  Date of birth
                </GovukTableHeaderCell>
                <GovukTableHeaderCell className="text-nowrap">
                  Date recorded
                </GovukTableHeaderCell>
                <GovukTableHeaderCell>
                  <span className={'govuk-visually-hidden'}>
                    Link to recording
                  </span>
                </GovukTableHeaderCell>
              </GovukTableRow>
            </GovukTableHead>
            <GovukTableBody>
              {transcriptions.map((transcription) => (
                <GovukTableRow key={transcription.id}>
                  <GovukTableCell>{transcription.client_name}</GovukTableCell>
                  <GovukTableCell>{transcription.case_id}</GovukTableCell>
                  <GovukTableCell>{transcription.title}</GovukTableCell>
                  <GovukTableCell>
                    {transcription.client_date_of_birth}
                  </GovukTableCell>
                  <GovukTableCell>
                    {formatRecordedDate(
                      transcription.date_of_recording ??
                        transcription.created_datetime
                    )}
                  </GovukTableCell>
                  <GovukTableCell>
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
          {(totalPages ?? 0) > 1 && (
            <div className="flex justify-center">
              <GovukPagination
                currentPage={currentPage}
                totalPages={totalPages!}
                getHref={(pageNumber: number) => {
                  const params = new URLSearchParams(searchParams)
                  params.set('page', String(pageNumber))
                  return hrefWithParams(pathname, params)
                }}
              />
            </div>
          )}
        </>
      )}
    </div>
  )
}
