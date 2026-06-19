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
  children,
  ...rest
}: Props) {
  return (
    <table className="govuk-table" {...rest}>
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
  children,
  ...rest
}: React.HTMLAttributes<HTMLTableSectionElement>) {
  return (
    <thead className="govuk-table__head" {...rest}>
      {children}
    </thead>
  )
}

export function GovukTableBody({
  children,
  ...rest
}: React.HTMLAttributes<HTMLTableSectionElement>) {
  return (
    <tbody className="govuk-table__body" {...rest}>
      {children}
    </tbody>
  )
}

export function GovukTableRow({
  children,
  ...rest
}: React.HTMLAttributes<HTMLTableRowElement>) {
  return (
    <tr className="govuk-table__row" {...rest}>
      {children}
    </tr>
  )
}

export function GovukTableHeaderCell({
  children,
  ...rest
}: React.ThHTMLAttributes<HTMLTableCellElement>) {
  return (
    <th className="govuk-table__header" {...rest}>
      {children}
    </th>
  )
}

export function GovukTableCell({
  children,
  ...rest
}: React.TdHTMLAttributes<HTMLTableCellElement>) {
  return (
    <td className="govuk-table__cell" {...rest}>
      {children}
    </td>
  )
}
