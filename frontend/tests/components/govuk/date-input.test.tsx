import { GovukDateInput } from '@/components/govuk/date-input'
import { render } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

describe('<GovukDateInput />', () => {
  it('renders the canonical date-input structure with the supplied id', () => {
    const { container } = render(
      <GovukDateInput id="dob" legend="Date of birth" />
    )
    expect(container.querySelector('.govuk-form-group')).not.toBeNull()
    expect(container.querySelector('.govuk-fieldset')).not.toBeNull()
    const dateInput = container.querySelector('.govuk-date-input')
    expect(dateInput).toHaveAttribute('id', 'dob')
  })

  it('renders day, month and year inputs with derived ids and names', () => {
    const { container } = render(
      <GovukDateInput id="dob" legend="Date of birth" />
    )
    for (const part of ['day', 'month', 'year']) {
      const input = container.querySelector(`#dob-${part}`) as HTMLInputElement
      expect(input).not.toBeNull()
      expect(input).toHaveAttribute('name', `dob-${part}`)
      expect(input).toHaveClass('govuk-date-input__input')
    }
  })

  it('associates each label with its input via htmlFor', () => {
    const { container } = render(
      <GovukDateInput id="dob" legend="Date of birth" />
    )
    const dayLabel = container.querySelector('label[for="dob-day"]')
    expect(dayLabel?.textContent).toBe('Day')
    const yearInput = container.querySelector('#dob-year')
    expect(yearInput).toHaveClass('govuk-input--width-4')
  })

  it('renders the legend text', () => {
    const { container } = render(
      <GovukDateInput id="dob" legend="Client date of birth (optional)" />
    )
    const legend = container.querySelector('.govuk-fieldset__legend')
    expect(legend?.textContent).toBe('Client date of birth (optional)')
  })

  it('wires an optional hint via aria-describedby', () => {
    const { container } = render(
      <GovukDateInput
        id="dob"
        legend="Date of birth"
        hint="For example, 27 3 2007"
      />
    )
    const hint = container.querySelector('.govuk-hint')
    expect(hint).toHaveAttribute('id', 'dob-hint')
    expect(container.querySelector('.govuk-fieldset')).toHaveAttribute(
      'aria-describedby',
      'dob-hint'
    )
  })
})
