import React from 'react'
import { cn } from '@/lib/utils'

type Props = {
  caption?: string
  captionSize?: 's' | 'm' | 'l'
  children: React.ReactNode
}

export function GovukTable({ caption, captionSize = 'm', children }: Props) {
  return (
    <table className="govuk-table">
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

export function GovukTableHead({ children }: { children: React.ReactNode }) {
  return <thead className="govuk-table__head">{children}</thead>
}

export function GovukTableBody({ children }: { children: React.ReactNode }) {
  return <tbody className="govuk-table__body">{children}</tbody>
}

export function GovukTableRow({ children }: { children: React.ReactNode }) {
  return <tr className="govuk-table__row">{children}</tr>
}

type CellProps = React.ThHTMLAttributes<HTMLTableCellElement> & {
  children: React.ReactNode
}

export function GovukTableHeaderCell({ children }: CellProps) {
  return <th className="govuk-table__header">{children}</th>
}

export function GovukTableCell({
  children,
}: React.TdHTMLAttributes<HTMLTableCellElement>) {
  return <td className="govuk-table__cell">{children}</td>
}
