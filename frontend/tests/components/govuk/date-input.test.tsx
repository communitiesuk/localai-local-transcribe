import {
  GovukDateInput,
  validateDateEntry,
} from '@/components/govuk/date-input'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type { ReactNode } from 'react'
import { FormProvider, type UseFormReturn, useForm } from 'react-hook-form'
import { describe, expect, it } from 'vitest'

type DateValue = {
  day: string
  month: string
  year: string
}

type Form = {
  date: DateValue
}
const validDate = { day: '27', month: '3', year: '2007' }

function DateInputProvider({
  children,
  defaultValues = { date: validDate },
  onReady,
}: {
  children: ReactNode
  defaultValues?: Form
  onReady?: (methods: UseFormReturn<Form>) => void
}) {
  const methods = useForm<Form>({
    defaultValues,
  })
  onReady?.(methods)

  return <FormProvider {...methods}>{children}</FormProvider>
}

describe('<GovukDateInput />', () => {
  it('renders the canonical date-input structure with the supplied id', () => {
    const { container } = render(
      <DateInputProvider>
        <GovukDateInput<Form> id="dob" name="date" legend="Date of birth" />
      </DateInputProvider>
    )
    expect(container.querySelector('.govuk-form-group')).not.toBeNull()
    expect(container.querySelector('.govuk-fieldset')).not.toBeNull()
    const dateInput = container.querySelector('.govuk-date-input')
    expect(dateInput).toHaveAttribute('id', 'dob')
  })

  it('renders day, month and year inputs with derived ids and names', () => {
    const { container } = render(
      <DateInputProvider>
        <GovukDateInput<Form> id="dob" name="date" legend="Date of birth" />
      </DateInputProvider>
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
      <DateInputProvider>
        <GovukDateInput<Form> id="dob" name="date" legend="Date of birth" />
      </DateInputProvider>
    )
    const dayLabel = container.querySelector('label[for="dob-day"]')
    expect(dayLabel?.textContent).toBe('Day')
    const yearInput = container.querySelector('#dob-year')
    expect(yearInput).toHaveClass('govuk-input--width-4')
  })

  it('renders the legend text', () => {
    const { container } = render(
      <DateInputProvider>
        <GovukDateInput<Form>
          id="dob"
          name="date"
          legend="Client date of birth (optional)"
        />
      </DateInputProvider>
    )
    const legend = container.querySelector('.govuk-fieldset__legend')
    expect(legend?.textContent).toBe('Client date of birth (optional)')
  })

  it('wires an optional hint via aria-describedby', () => {
    const { container } = render(
      <DateInputProvider>
        <GovukDateInput<Form>
          id="dob"
          name="date"
          legend="Date of birth"
          hint="For example, 27 3 2007"
        />
      </DateInputProvider>
    )
    const hint = container.querySelector('.govuk-hint')
    expect(hint).toHaveAttribute('id', 'dob-hint')
    expect(container.querySelector('.govuk-fieldset')).toHaveAttribute(
      'aria-describedby',
      'dob-hint'
    )
  })

  it('integrates with react-hook-form', async () => {
    let form: UseFormReturn<Form> | undefined

    render(
      <DateInputProvider
        defaultValues={{ date: { day: '', month: '', year: '' } }}
        onReady={(methods) => {
          form = methods
        }}
      >
        <GovukDateInput<Form> id="dob" name="date" legend="Date of birth" />
      </DateInputProvider>
    )

    await userEvent.type(screen.getByLabelText('Day'), '1')
    await userEvent.type(screen.getByLabelText('Month'), '2')
    await userEvent.type(screen.getByLabelText('Year'), '2026')

    expect(form?.getValues()).toEqual({
      date: { day: '1', month: '2', year: '2026' },
    })
  })

  it('shows validation errors for missing date fields', () => {
    render(
      <DateInputProvider
        defaultValues={{
          date: { day: '', month: '', year: '2026' },
        }}
      >
        <GovukDateInput<Form> id="dob" name="date" legend="Date of birth" />
      </DateInputProvider>
    )

    expect(
      screen.getByText('The date must include a day and month')
    ).toHaveClass('govuk-error-message')
    expect(screen.getByLabelText('Day')).toHaveAttribute('aria-invalid', 'true')
    expect(screen.getByLabelText('Month')).toHaveAttribute(
      'aria-invalid',
      'true'
    )
    expect(screen.getByLabelText('Year')).not.toHaveAttribute('aria-invalid')
  })
})

describe('validateDateEntry', () => {
  function dateValueFromDate(date: Date): DateValue {
    return {
      day: String(date.getDate()),
      month: String(date.getMonth() + 1),
      year: String(date.getFullYear()),
    }
  }

  it('returns null for a valid real date', () => {
    expect(
      validateDateEntry({ day: '29', month: '2', year: '2024' })
    ).toBeNull()
  })

  it('returns missing fields in the error message and field list', () => {
    expect(validateDateEntry({ day: '', month: '', year: '2026' })).toEqual({
      message: 'The date must include a day and month',
      fields: ['day', 'month'],
    })
  })

  it('uses the supplied description in validation messages', () => {
    expect(
      validateDateEntry({ day: '', month: '3', year: '2026' }, undefined, 'DOB')
    ).toEqual({
      message: 'The DOB must include a day',
      fields: ['day'],
    })
  })

  it('returns an error when the date is not real', () => {
    expect(validateDateEntry({ day: '31', month: '2', year: '2026' })).toEqual({
      message: 'The date must be a real date',
      fields: ['day', 'month', 'year'],
    })
  })

  it('returns an error when a past date is required but the date is in the future', () => {
    const tomorrow = new Date()
    tomorrow.setDate(tomorrow.getDate() + 1)

    expect(validateDateEntry(dateValueFromDate(tomorrow), 'past')).toEqual({
      message: 'The date must be in the past',
      fields: ['day', 'month', 'year'],
    })
  })

  it('returns an error when a future date is required but the date is in the past', () => {
    const yesterday = new Date()
    yesterday.setDate(yesterday.getDate() - 1)

    expect(validateDateEntry(dateValueFromDate(yesterday), 'future')).toEqual({
      message: 'The date must be in the future',
      fields: ['day', 'month', 'year'],
    })
  })
})
