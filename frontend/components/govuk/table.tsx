import React from 'react'
import { cn } from '@/lib/utils'

type Props = {
  caption?: string
  captionSize?: 's' | 'm' | 'l'
  children: React.ReactNode
} & React.TableHTMLAttributes<HTMLTableElement>

export function GovukTable({
  caption,
  captionSize = 'm',
  className,
  children,
  ...rest
}: Props) {
  return (
    <table className={cn('govuk-table', className)} {...rest}>
      {caption && (
        <caption
          className={cn(
            'govuk-table__caption',
            `govuk-table__caption--${captionSize}`
          )}
        >
          {caption}
        </caption>
      )}

      {children}
    </table>
  )
}

export function GovukTableHead({
  className,
  children,
  ...rest
}: React.HTMLAttributes<HTMLTableSectionElement>) {
  return (
    <thead className={cn('govuk-table__head', className)} {...rest}>
      {children}
    </thead>
  )
}

export function GovukTableBody({
  className,
  children,
  ...rest
}: React.HTMLAttributes<HTMLTableSectionElement>) {
  return (
    <tbody className={cn('govuk-table__body', className)} {...rest}>
      {children}
    </tbody>
  )
}

export function GovukTableRow({
  className,
  children,
  ...rest
}: React.HTMLAttributes<HTMLTableRowElement>) {
  return (
    <tr className={cn('govuk-table__row', className)} {...rest}>
      {children}
    </tr>
  )
}

type GovukTableHeaderCellProps = {
  isNumeric?: boolean
} & React.ThHTMLAttributes<HTMLTableCellElement>

export function GovukTableHeaderCell({
  isNumeric,
  className,
  children,
  ...rest
}: GovukTableHeaderCellProps) {
  return (
    <th
      className={cn(
        'govuk-table__header',
        isNumeric && 'govuk-table__header--numeric',
        className
      )}
      {...rest}
    >
      {children}
    </th>
  )
}

type GovukTableCellProps = {
  isNumeric?: boolean
} & React.TdHTMLAttributes<HTMLTableCellElement>

export function GovukTableCell({
  isNumeric,
  className,
  children,
  ...rest
}: GovukTableCellProps) {
  return (
    <td
      className={cn(
        'govuk-table__cell',
        isNumeric && 'govuk-table__cell--numeric',
        className
      )}
      {...rest}
    >
      {children}
    </td>
  )
}
