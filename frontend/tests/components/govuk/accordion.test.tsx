import { GovukAccordion } from '@/components/govuk/accordion'
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

describe('<GovukAccordion />', () => {
  it('renders a div with the canonical govuk-accordion class and data-module', () => {
    const { container } = render(
      <GovukAccordion id="accordion-test">
        <GovukAccordion.Section heading="Section one">
          <p>Content</p>
        </GovukAccordion.Section>
      </GovukAccordion>
    )
    const root = container.firstElementChild as HTMLElement
    expect(root.tagName).toBe('DIV')
    expect(root).toHaveClass('govuk-accordion')
    expect(root).toHaveAttribute('data-module', 'govuk-accordion')
  })

  it('sets the supplied id on the root element', () => {
    const { container } = render(
      <GovukAccordion id="my-accordion">
        <GovukAccordion.Section heading="A">
          <p>Body</p>
        </GovukAccordion.Section>
      </GovukAccordion>
    )
    expect(container.firstElementChild).toHaveAttribute('id', 'my-accordion')
  })

  it('renders a Section with the canonical section structure', () => {
    const { container } = render(
      <GovukAccordion id="accordion-test">
        <GovukAccordion.Section heading="Section heading">
          <p>Section body</p>
        </GovukAccordion.Section>
      </GovukAccordion>
    )
    expect(container.querySelector('.govuk-accordion__section')).not.toBeNull()
    expect(
      container.querySelector('.govuk-accordion__section-header')
    ).not.toBeNull()
    expect(
      container.querySelector('.govuk-accordion__section-heading')
    ).not.toBeNull()
    expect(
      container.querySelector('.govuk-accordion__section-button')
    ).not.toBeNull()
    expect(
      container.querySelector('.govuk-accordion__section-content')
    ).not.toBeNull()
  })

  it('renders the Section heading text inside the button span', () => {
    render(
      <GovukAccordion id="accordion-test">
        <GovukAccordion.Section heading="My heading">
          <p>Body</p>
        </GovukAccordion.Section>
      </GovukAccordion>
    )
    const btn = screen.getByText('My heading')
    expect(btn.tagName).toBe('SPAN')
    expect(btn).toHaveClass('govuk-accordion__section-button')
  })

  it('defaults Section heading to an h2', () => {
    const { container } = render(
      <GovukAccordion id="accordion-test">
        <GovukAccordion.Section heading="Heading">
          <p>Body</p>
        </GovukAccordion.Section>
      </GovukAccordion>
    )
    expect(
      container.querySelector('h2.govuk-accordion__section-heading')
    ).not.toBeNull()
  })

  it('renders Section heading at the specified heading level', () => {
    const { container } = render(
      <GovukAccordion id="accordion-test">
        <GovukAccordion.Section heading="Heading" headingLevel={3}>
          <p>Body</p>
        </GovukAccordion.Section>
      </GovukAccordion>
    )
    expect(
      container.querySelector('h3.govuk-accordion__section-heading')
    ).not.toBeNull()
  })

  it('renders Section children inside the content wrapper', () => {
    const { container } = render(
      <GovukAccordion id="accordion-test">
        <GovukAccordion.Section heading="Heading">
          <p>Section body text</p>
        </GovukAccordion.Section>
      </GovukAccordion>
    )
    const content = container.querySelector(
      '.govuk-accordion__section-content'
    ) as HTMLElement
    expect(content.textContent).toBe('Section body text')
  })

  it('composes a caller-supplied className on the accordion root', () => {
    const { container } = render(
      <GovukAccordion id="accordion-test" className="mt-4">
        <GovukAccordion.Section heading="A">
          <p>B</p>
        </GovukAccordion.Section>
      </GovukAccordion>
    )
    expect(container.firstElementChild).toHaveClass('govuk-accordion', 'mt-4')
  })

  it('forwards arbitrary HTML attributes on the accordion root', () => {
    render(
      <GovukAccordion id="accordion-test" data-testid="my-accordion">
        <GovukAccordion.Section heading="A">
          <p>B</p>
        </GovukAccordion.Section>
      </GovukAccordion>
    )
    expect(screen.getByTestId('my-accordion')).toBeInTheDocument()
  })
})
