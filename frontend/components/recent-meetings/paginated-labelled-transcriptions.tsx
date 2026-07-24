'use client'

import { OfflineRecordings } from '@/components/recent-meetings/offline-recordings'
import { TranscriptionListItem } from '@/components/recent-meetings/transcription-list-item'
import { Button } from '@/components/ui/button'
import { listLabelledTranscriptionsTranscriptionsLabelledGetOptions } from '@/lib/client/@tanstack/react-query.gen'
import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { ChevronLeft, ChevronRight, Info } from 'lucide-react'
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
  const {
    data: paginatedResponse,
    isLoading,
    error,
  } = useQuery({
    ...listLabelledTranscriptionsTranscriptionsLabelledGetOptions({
      query: { page: currentPage, page_size: pageSize },
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
    router.replace(pathname + `?page=${paginatedResponse.total_pages}`)
  }
  const transcriptions = paginatedResponse?.items || []
  const totalPages = paginatedResponse?.total_pages || 1
  const totalCount = paginatedResponse?.total_count || 0

  return (
    <div>
      <OfflineRecordings />
      <GovukHeading as="h2" size="m">
        Labelled recordings
      </GovukHeading>
      <GovukHint>Total: {totalCount}</GovukHint>
      {isLoading ? (
        <div className="flex items-center justify-center py-8">
          <div className="text-gray-500">Loading transcriptions...</div>
        </div>
      ) : error ? (
        <div className="flex items-center justify-center py-8">
          <div className="text-red-500">Error loading transcriptions</div>
        </div>
      ) : transcriptions.length === 0 ? (
        <div className="flex items-center justify-center py-8">
          <div className="text-gray-500">No transcriptions found</div>
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
                    {transcription.date_of_recording}
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
          {totalPages > 1 && (
            <div className="flex items-center justify-center space-x-2">
              {currentPage > 1 && (
                <Button variant="outline" size="sm" asChild>
                  <Link
                    href={pathname + `?page=${currentPage - 1}`}
                    scroll={false}
                  >
                    <ChevronLeft className="h-4 w-4" />
                    Previous
                  </Link>
                </Button>
              )}
              {getPageNumbers(currentPage, totalPages).map((page) => (
                <Button
                  key={page}
                  variant={currentPage === page ? 'default' : 'outline'}
                  size="sm"
                  className="min-w-10"
                  asChild
                >
                  <Link href={pathname + `?page=${page}`} scroll={false}>
                    {page}
                  </Link>
                </Button>
              ))}
              {currentPage < totalPages && (
                <Button variant="outline" size="sm" asChild>
                  <Link
                    href={pathname + `?page=${currentPage + 1}`}
                    scroll={false}
                  >
                    Next
                    <ChevronRight className="h-4 w-4" />
                  </Link>
                </Button>
              )}
            </div>
          )}
          <div className="mt-4 text-center text-sm text-gray-500">
            Page {currentPage} of {totalPages}
          </div>
        </>
      )}
    </div>
  )
}
