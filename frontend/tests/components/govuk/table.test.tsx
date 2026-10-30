import {
  GovukTable,
  GovukTableHead,
  GovukTableBody,
  GovukTableRow,
  GovukTableHeaderCell,
  GovukTableCell,
} from '@/components/govuk/table'
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

describe('<GovukTable />', () => {
  it('renders a <table> with the govuk-table class', () => {
    const { container } = render(
      <GovukTable>
        <GovukTableBody />
      </GovukTable>
    )
    const root = container.firstElementChild as HTMLElement
    expect(root.tagName).toBe('TABLE')
    expect(root).toHaveClass('govuk-table')
  })

  it('renders no caption by default', () => {
    const { container } = render(
      <GovukTable>
        <GovukTableBody />
      </GovukTable>
    )
    expect(container.querySelector('caption')).toBeNull()
  })

  it('renders a caption with the default medium size modifier', () => {
    const { container } = render(
      <GovukTable caption="Dates and amounts">
        <GovukTableBody />
      </GovukTable>
    )
    const caption = container.querySelector('caption') as HTMLElement
    expect(caption).toHaveTextContent('Dates and amounts')
    expect(caption).toHaveClass(
      'govuk-table__caption',
      'govuk-table__caption--m'
    )
  })

  it('renders a caption with the requested size modifier', () => {
    const { container } = render(
      <GovukTable caption="Dates" captionSize="l">
        <GovukTableBody />
      </GovukTable>
    )
    const caption = container.querySelector('caption') as HTMLElement
    expect(caption).toHaveClass('govuk-table__caption--l')
  })

  it('composes a caller-supplied className without dropping govuk-table', () => {
    const { container } = render(
      <GovukTable className="govuk-!-margin-bottom-2">
        <GovukTableBody />
      </GovukTable>
    )
    const root = container.firstElementChild as HTMLElement
    expect(root).toHaveClass('govuk-table', 'govuk-!-margin-bottom-2')
  })

  it('forwards arbitrary HTML attributes via spread', () => {
    render(
      <GovukTable data-testid="my-table">
        <GovukTableBody />
      </GovukTable>
    )
    expect(screen.getByTestId('my-table')).toBeInTheDocument()
  })
})

describe('<GovukTableHead />', () => {
  it('renders a <thead> with the govuk-table__head class', () => {
    const { container } = render(
      <table>
        <GovukTableHead />
      </table>
    )
    const head = container.querySelector('thead') as HTMLElement
    expect(head).toHaveClass('govuk-table__head')
  })

  it('composes a caller-supplied className without dropping govuk-table__head', () => {
    const { container } = render(
      <table>
        <GovukTableHead className="extra-head" />
      </table>
    )
    const head = container.querySelector('thead') as HTMLElement
    expect(head).toHaveClass('govuk-table__head', 'extra-head')
  })
})

describe('<GovukTableBody />', () => {
  it('renders a <tbody> with the govuk-table__body class', () => {
    const { container } = render(
      <table>
        <GovukTableBody />
      </table>
    )
    const body = container.querySelector('tbody') as HTMLElement
    expect(body).toHaveClass('govuk-table__body')
  })

  it('composes a caller-supplied className without dropping govuk-table__body', () => {
    const { container } = render(
      <table>
        <GovukTableBody className="extra-body" />
      </table>
    )
    const body = container.querySelector('tbody') as HTMLElement
    expect(body).toHaveClass('govuk-table__body', 'extra-body')
  })
})

describe('<GovukTableRow />', () => {
  it('renders a <tr> with the govuk-table__row class', () => {
    const { container } = render(
      <table>
        <tbody>
          <GovukTableRow />
        </tbody>
      </table>
    )
    const row = container.querySelector('tr') as HTMLElement
    expect(row).toHaveClass('govuk-table__row')
  })

  it('composes a caller-supplied className without dropping govuk-table__row', () => {
    const { container } = render(
      <table>
        <tbody>
          <GovukTableRow className="extra-row" />
        </tbody>
      </table>
    )
    const row = container.querySelector('tr') as HTMLElement
    expect(row).toHaveClass('govuk-table__row', 'extra-row')
  })
})

describe('<GovukTableHeaderCell />', () => {
  it('renders a <th> with the govuk-table__header class', () => {
    const { container } = render(
      <table>
        <thead>
          <tr>
            <GovukTableHeaderCell>Name</GovukTableHeaderCell>
          </tr>
        </thead>
      </table>
    )
    const cell = container.querySelector('th') as HTMLElement
    expect(cell).toHaveTextContent('Name')
    expect(cell).toHaveClass('govuk-table__header')
  })

  it('composes a caller-supplied className without dropping govuk-table__header', () => {
    const { container } = render(
      <table>
        <thead>
          <tr>
            <GovukTableHeaderCell className="govuk-table__header--numeric">
              Amount
            </GovukTableHeaderCell>
          </tr>
        </thead>
      </table>
    )
    const cell = container.querySelector('th') as HTMLElement
    expect(cell).toHaveClass(
      'govuk-table__header',
      'govuk-table__header--numeric'
    )
  })
})

describe('<GovukTableCell />', () => {
  it('renders a <td> with the govuk-table__cell class', () => {
    const { container } = render(
      <table>
        <tbody>
          <tr>
            <GovukTableCell>Alpha</GovukTableCell>
          </tr>
        </tbody>
      </table>
    )
    const cell = container.querySelector('td') as HTMLElement
    expect(cell).toHaveTextContent('Alpha')
    expect(cell).toHaveClass('govuk-table__cell')
  })

  it('composes a caller-supplied className without dropping govuk-table__cell', () => {
    const { container } = render(
      <table>
        <tbody>
          <tr>
            <GovukTableCell className="govuk-table__cell--numeric">
              100
            </GovukTableCell>
          </tr>
        </tbody>
      </table>
    )
    const cell = container.querySelector('td') as HTMLElement
    expect(cell).toHaveClass('govuk-table__cell', 'govuk-table__cell--numeric')
  })
})
