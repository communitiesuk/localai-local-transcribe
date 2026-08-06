import { cn } from '@/lib/utils'

import Link from 'next/link'

type Props = {
  currentPage: number
  totalPages: number
  getHref: (page: number) => string
  /** Window the list around the current page instead of listing every page. */
  maxPagesToShow?: number
  scroll?: boolean
}

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

export function GovukPagination({
  currentPage,
  totalPages,
  getHref,
  maxPagesToShow,
  scroll = true,
}: Props) {
  const pages = maxPagesToShow
    ? getPageNumbers(currentPage, totalPages, maxPagesToShow)
    : Array.from({ length: totalPages }, (_, i) => i + 1)

  return (
    <nav className="govuk-pagination" aria-label="Pagination">
      {currentPage > 1 && (
        <div className="govuk-pagination__prev">
          <Link
            className="govuk-link govuk-pagination__link"
            href={getHref(currentPage - 1)}
            rel="prev"
            scroll={scroll}
          >
            <svg
              className="govuk-pagination__icon govuk-pagination__icon--prev"
              xmlns="http://www.w3.org/2000/svg"
              height="13"
              width="15"
              aria-hidden="true"
              focusable="false"
              viewBox="0 0 15 13"
            >
              <path d="m6.5938-0.0078125-6.7266 6.7266 6.7441 6.4062 1.377-1.449-4.1856-3.9768h12.896v-2h-12.984l4.2931-4.293-1.414-1.414z"></path>
            </svg>
            <span className="govuk-pagination__link-title">
              Previous<span className="govuk-visually-hidden"> page</span>
            </span>
          </Link>
        </div>
      )}
      <ul className="govuk-pagination__list">
        {pages.map((page) => (
          <li
            key={page}
            className={cn(
              'govuk-pagination__item',
              page === currentPage && 'govuk-pagination__item--current'
            )}
          >
            <Link
              className="govuk-link govuk-pagination__link"
              href={getHref(page)}
              aria-label={`Page ${page}`}
              aria-current={page === currentPage ? 'page' : undefined}
              scroll={scroll}
            >
              {page}
            </Link>
          </li>
        ))}
      </ul>
      {currentPage < totalPages && (
        <div className="govuk-pagination__next">
          <Link
            className="govuk-link govuk-pagination__link"
            href={getHref(currentPage + 1)}
            rel="next"
            scroll={scroll}
          >
            <span className="govuk-pagination__link-title">
              Next<span className="govuk-visually-hidden"> page</span>
            </span>
            <svg
              className="govuk-pagination__icon govuk-pagination__icon--next"
              xmlns="http://www.w3.org/2000/svg"
              height="13"
              width="15"
              aria-hidden="true"
              focusable="false"
              viewBox="0 0 15 13"
            >
              <path d="m8.107-0.0078125-1.4136 1.414 4.2926 4.293h-12.986v2h12.896l-4.1855 3.9766 1.377 1.4492 6.7441-6.4062-6.7246-6.7266z"></path>
            </svg>
          </Link>
        </div>
      )}
    </nav>
  )
}
