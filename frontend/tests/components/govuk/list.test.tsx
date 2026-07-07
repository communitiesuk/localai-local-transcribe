import { GovukList, GovukListItem } from '@/components/govuk/list'
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

describe('<GovukList />', () => {
  it('renders a <ul> with the govuk-list class by default', () => {
    const { container } = render(
      <GovukList>
        <GovukListItem>Alpha</GovukListItem>
      </GovukList>
    )
    const root = container.firstElementChild as HTMLElement
    expect(root.tagName).toBe('UL')
    expect(root.className).toBe('govuk-list')
  })

  it('renders an <ol> with number modifier when type is "number"', () => {
    const { container } = render(
      <GovukList type="number">
        <GovukListItem>One</GovukListItem>
      </GovukList>
    )
    const root = container.firstElementChild as HTMLElement
    expect(root.tagName).toBe('OL')
    expect(root).toHaveClass('govuk-list', 'govuk-list--number')
  })

  it('renders an <ul> with number modifier when type is "bullet"', () => {
    const { container } = render(
      <GovukList type="bullet">
        <GovukListItem>Item</GovukListItem>
      </GovukList>
    )
    const root = container.firstElementChild as HTMLElement
    expect(root.tagName).toBe('UL')
    expect(root).toHaveClass('govuk-list', 'govuk-list--bullet')
  })

  it('applies the govuk-list--spaced modifier', () => {
    const { container } = render(
      <GovukList spaced>
        <GovukListItem>Item</GovukListItem>
      </GovukList>
    )
    const root = container.firstElementChild as HTMLElement
    expect(root).toHaveClass('govuk-list', 'govuk-list--spaced')
  })

  it('composes a caller-supplied className without clobbering the canonical class', () => {
    const { container } = render(
      <GovukList className="govuk-!-margin-bottom-2">
        <GovukListItem>Item</GovukListItem>
      </GovukList>
    )
    const root = container.firstElementChild as HTMLElement
    expect(root).toHaveClass('govuk-list', 'govuk-!-margin-bottom-2')
  })

  it('forwards arbitrary HTML attributes via spread', () => {
    render(
      <GovukList data-testid="my-list">
        <GovukListItem>Item</GovukListItem>
      </GovukList>
    )
    expect(screen.getByTestId('my-list')).toBeInTheDocument()
  })
})

describe('<GovukListItem />', () => {
  it('renders a plain <li> with no class by default', () => {
    const { container } = render(<GovukListItem>Item</GovukListItem>)
    const item = container.firstElementChild as HTMLElement
    expect(item.tagName).toBe('LI')
    expect(item.hasAttribute('class')).toBe(false)
  })

  it('renders children and forwards arbitrary HTML attributes via spread', () => {
    render(<GovukListItem data-testid="item">Beta</GovukListItem>)
    const item = screen.getByTestId('item')
    expect(item).toHaveTextContent('Beta')
  })
})
