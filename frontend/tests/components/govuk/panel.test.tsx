import { render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import {
  GovukPanel,
  GovukPanelHeader,
  GovukPanelTitle,
  GovukPanelDescription,
  GovukPanelContent,
  GovukPanelFooter,
} from '@/components/govuk/panel'

describe('GovukPanel', () => {
  it('renders a panel with header, description and content', () => {
    render(
      <GovukPanel padding={4} border>
        <GovukPanelHeader>
          <GovukPanelTitle>Test panel</GovukPanelTitle>
          <GovukPanelDescription>Panel description</GovukPanelDescription>
        </GovukPanelHeader>
        <GovukPanelContent>
          <p>Panel body text</p>
        </GovukPanelContent>
      </GovukPanel>
    )

    expect(screen.getByText('Test panel')).toBeInTheDocument()
    expect(screen.getByText('Panel description')).toBeInTheDocument()
    expect(screen.getByText('Panel body text')).toBeInTheDocument()
  })

  it('applies a custom class name to the panel wrapper', () => {
    const { container } = render(
      <GovukPanel padding={4} border className="custom-panel">
        <GovukPanelHeader>
          <GovukPanelTitle>Custom class panel</GovukPanelTitle>
        </GovukPanelHeader>
      </GovukPanel>
    )

    expect(container.firstChild).toHaveClass('custom-panel')
  })

  it('renders GovukPanelTitle as a heading element', () => {
    render(
      <GovukPanel padding={4} border>
        <GovukPanelHeader>
          <GovukPanelTitle>Panel title heading</GovukPanelTitle>
        </GovukPanelHeader>
      </GovukPanel>
    )

    const title = screen.getByText('Panel title heading')
    expect(title.tagName).toMatch(/^H[1-6]$/)
  })

  it('renders GovukPanelDescription inside the header region', () => {
    render(
      <GovukPanel padding={4} border>
        <GovukPanelHeader>
          <GovukPanelTitle>Header title</GovukPanelTitle>
          <GovukPanelDescription>Description text</GovukPanelDescription>
        </GovukPanelHeader>
      </GovukPanel>
    )

    const header = screen.getByText('Header title').closest('div')
    expect(header).toBeTruthy()
    expect(
      within(header as HTMLElement).getByText('Description text')
    ).toBeInTheDocument()
  })

  it('renders GovukPanelContent children correctly within content area', () => {
    render(
      <GovukPanel padding={4} border>
        <GovukPanelHeader>
          <GovukPanelTitle>Content test</GovukPanelTitle>
        </GovukPanelHeader>
        <GovukPanelContent>
          <span data-testid="panel-content">Panel content area</span>
        </GovukPanelContent>
      </GovukPanel>
    )

    expect(screen.getByTestId('panel-content')).toBeInTheDocument()
    expect(screen.getByText('Panel content area')).toBeInTheDocument()
  })

  it('renders GovukPanelFooter with the footer slot and custom class names', () => {
    render(
      <GovukPanel padding={4} border>
        <GovukPanelHeader>
          <GovukPanelTitle>Footer test</GovukPanelTitle>
        </GovukPanelHeader>
        <GovukPanelContent>Content</GovukPanelContent>
        <GovukPanelFooter
          className="extra-footer-class"
          data-testid="panel-footer"
        >
          Footer content
        </GovukPanelFooter>
      </GovukPanel>
    )

    const footer = screen.getByTestId('panel-footer')
    expect(footer).toHaveAttribute('data-slot', 'govuk-panel-footer')
    expect(footer).toHaveClass('govuk-!-margin-top-4')
    expect(footer).toHaveClass('extra-footer-class')
    expect(footer).toHaveTextContent('Footer content')
  })
})
