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

export function GovukTableHeaderCell({
  className,
  children,
  ...rest
}: React.ThHTMLAttributes<HTMLTableCellElement>) {
  return (
    <th className={cn('govuk-table__header', className)} {...rest}>
      {children}
    </th>
  )
}

export function GovukTableCell({
  className,
  children,
  ...rest
}: React.TdHTMLAttributes<HTMLTableCellElement>) {
  return (
    <td className={cn('govuk-table__cell', className)} {...rest}>
      {children}
    </td>
  )
}
