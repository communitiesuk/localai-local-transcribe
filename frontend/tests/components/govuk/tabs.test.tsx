import { GovukTabs } from '@/components/govuk/tabs'
import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

describe('<GovukTabs />', () => {
  it('renders a div with the canonical govuk-tabs class and data-module', () => {
    const { container } = render(
      <GovukTabs id="tabs-test">
        <GovukTabs.Panel id="one" label="One">
          <p>Panel one</p>
        </GovukTabs.Panel>
      </GovukTabs>
    )
    const root = container.querySelector(
      '[data-module="govuk-tabs"]'
    ) as HTMLElement
    expect(root.tagName).toBe('DIV')
    expect(root).toHaveClass('govuk-tabs')
    expect(root).toHaveAttribute('id', 'tabs-test')
  })

  it('renders a tab link per panel pointing at the panel id', () => {
    const { container } = render(
      <GovukTabs id="tabs-test">
        <GovukTabs.Panel id="transcript" label="Transcript">
          <p>A</p>
        </GovukTabs.Panel>
        <GovukTabs.Panel id="summary" label="Meeting summary">
          <p>B</p>
        </GovukTabs.Panel>
      </GovukTabs>
    )
    const tabs = container.querySelectorAll('.govuk-tabs__tab')
    expect(tabs).toHaveLength(2)
    expect(tabs[0]).toHaveAttribute('href', '#transcript')
    expect(tabs[0].textContent).toBe('Transcript')
    expect(tabs[1]).toHaveAttribute('href', '#summary')
  })

  it('marks only the first list item as selected', () => {
    const { container } = render(
      <GovukTabs id="tabs-test">
        <GovukTabs.Panel id="one" label="One">
          <p>A</p>
        </GovukTabs.Panel>
        <GovukTabs.Panel id="two" label="Two">
          <p>B</p>
        </GovukTabs.Panel>
      </GovukTabs>
    )
    const items = container.querySelectorAll('.govuk-tabs__list-item')
    expect(items[0]).toHaveClass('govuk-tabs__list-item--selected')
    expect(items[1]).not.toHaveClass('govuk-tabs__list-item--selected')
  })

  it('supports arrow key navigation between tabs', () => {
    render(
      <GovukTabs id="tabs-test">
        <GovukTabs.Panel id="one" label="One">
          <p>A</p>
        </GovukTabs.Panel>
        <GovukTabs.Panel id="two" label="Two">
          <p>B</p>
        </GovukTabs.Panel>
        <GovukTabs.Panel id="three" label="Three">
          <p>C</p>
        </GovukTabs.Panel>
      </GovukTabs>
    )

    const one = screen.getByRole('tab', { name: 'One' })
    const two = screen.getByRole('tab', { name: 'Two' })
    const three = screen.getByRole('tab', { name: 'Three' })

    fireEvent.keyDown(one, { key: 'ArrowRight' })
    expect(two).toHaveAttribute('aria-selected', 'true')
    expect(two).toHaveFocus()

    fireEvent.keyDown(two, { key: 'ArrowLeft' })
    expect(one).toHaveAttribute('aria-selected', 'true')
    expect(one).toHaveFocus()

    fireEvent.keyDown(one, { key: 'ArrowLeft' })
    expect(three).toHaveAttribute('aria-selected', 'true')
    expect(three).toHaveFocus()
  })

  it('supports Home and End keyboard navigation', () => {
    render(
      <GovukTabs id="tabs-test">
        <GovukTabs.Panel id="one" label="One">
          <p>A</p>
        </GovukTabs.Panel>
        <GovukTabs.Panel id="two" label="Two">
          <p>B</p>
        </GovukTabs.Panel>
        <GovukTabs.Panel id="three" label="Three">
          <p>C</p>
        </GovukTabs.Panel>
      </GovukTabs>
    )

    const one = screen.getByRole('tab', { name: 'One' })
    const three = screen.getByRole('tab', { name: 'Three' })

    fireEvent.keyDown(one, { key: 'End' })
    expect(three).toHaveAttribute('aria-selected', 'true')
    expect(three).toHaveFocus()

    fireEvent.keyDown(three, { key: 'Home' })
    expect(one).toHaveAttribute('aria-selected', 'true')
    expect(one).toHaveFocus()
  })

  it('keeps Enter and Space selecting the active tab', () => {
    render(
      <GovukTabs id="tabs-test">
        <GovukTabs.Panel id="one" label="One">
          <p>A</p>
        </GovukTabs.Panel>
        <GovukTabs.Panel id="two" label="Two">
          <p>B</p>
        </GovukTabs.Panel>
      </GovukTabs>
    )

    const one = screen.getByRole('tab', { name: 'One' })

    fireEvent.keyDown(one, { key: 'Enter' })
    expect(one).toHaveAttribute('aria-selected', 'true')

    fireEvent.keyDown(one, { key: ' ' })
    expect(one).toHaveAttribute('aria-selected', 'true')
  })

  it('renders each panel with its id and hides all but the first', () => {
    const { container } = render(
      <GovukTabs id="tabs-test">
        <GovukTabs.Panel id="one" label="One">
          <p>Panel one body</p>
        </GovukTabs.Panel>
        <GovukTabs.Panel id="two" label="Two">
          <p>Panel two body</p>
        </GovukTabs.Panel>
      </GovukTabs>
    )
    const panels = container.querySelectorAll('.govuk-tabs__panel')
    expect(panels[0]).toHaveAttribute('id', 'one')
    expect(panels[0]).not.toHaveClass('govuk-tabs__panel--hidden')
    expect(panels[1]).toHaveAttribute('id', 'two')
    expect(panels[1]).toHaveClass('govuk-tabs__panel--hidden')
  })

  it('renders the panels as siblings of the tab list, not inside it', () => {
    const { container } = render(
      <GovukTabs id="tabs-test">
        <GovukTabs.Panel id="one" label="One">
          <p>A</p>
        </GovukTabs.Panel>
      </GovukTabs>
    )
    expect(
      container.querySelector('.govuk-tabs__list .govuk-tabs__panel')
    ).toBeNull()
  })

  it('defaults the title to Contents', () => {
    render(
      <GovukTabs id="tabs-test">
        <GovukTabs.Panel id="one" label="One">
          <p>A</p>
        </GovukTabs.Panel>
      </GovukTabs>
    )
    const title = screen.getByText('Contents')
    expect(title).toHaveClass('govuk-tabs__title')
  })
})
