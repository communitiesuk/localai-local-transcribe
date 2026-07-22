'use client'

import { OfflineRecordings } from '@/components/recent-meetings/offline-recordings'
import { TranscriptionListItem } from '@/components/recent-meetings/transcription-list-item'
import {
  getUserUsersMeGetOptions,
  listTranscriptionsTranscriptionsGetOptions,
} from '@/lib/client/@tanstack/react-query.gen'
import { GovukPagination } from '@/components/govuk/pagination'
import { conditionalPluralSuffix } from '@/lib/utils'
import { keepPreviousData, useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { usePathname, useRouter, useSearchParams } from 'next/navigation'

export const PaginatedTranscriptions = () => {
  const { data: user } = useQuery({ ...getUserUsersMeGetOptions() })
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
    ...listTranscriptionsTranscriptionsGetOptions({
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
      <div className="govuk-!-margin-bottom-4">
        <div className="flex items-baseline justify-between">
          <h1 className="govuk-heading-l govuk-!-margin-bottom-0">
            Recent meetings
          </h1>
          <span className="govuk-body-s govuk-!-margin-bottom-0">
            {totalCount} transcription{conditionalPluralSuffix(totalCount)}
          </span>
        </div>
        {user && user.data_retention_days && (
          <p className="govuk-body-s govuk-!-margin-top-2 govuk-!-margin-bottom-0">
            Your data retention period is set to {user.data_retention_days} day
            {conditionalPluralSuffix(user.data_retention_days)}. Change this in{' '}
            <Link href="/settings" className="govuk-link">
              settings
            </Link>
            .
          </p>
        )}
      </div>
      {isLoading ? (
        <p className="govuk-body">Loading transcriptions...</p>
      ) : error ? (
        <p className="govuk-body">Error loading transcriptions.</p>
      ) : transcriptions.length === 0 ? (
        <p className="govuk-body">No transcriptions found.</p>
      ) : (
        <>
          <ul className="govuk-!-margin-bottom-6 flex flex-col gap-2">
            {transcriptions.map((transcription) => (
              <TranscriptionListItem
                transcription={transcription}
                key={transcription.id}
              />
            ))}
          </ul>
          {totalPages > 1 && (
            <GovukPagination
              currentPage={currentPage}
              totalPages={totalPages}
              getHref={(page) => `${pathname}?page=${page}`}
              maxPagesToShow={5}
              scroll={false}
            />
          )}
        </>
      )}
    </div>
  )
}
