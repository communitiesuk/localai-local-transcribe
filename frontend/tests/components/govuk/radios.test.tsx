import { GovukRadios } from '@/components/govuk/radios'
import { act, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useEffect, useState } from 'react'
import { Controller, useForm } from 'react-hook-form'
import { describe, expect, it, vi } from 'vitest'

describe('<GovukRadios />', () => {
  const options = [
    { label: 'England', value: 'england' },
    { label: 'Scotland', value: 'scotland' },
    { label: 'Wales', value: 'wales' },
  ]

  it('renders the canonical govuk-radios container with no data-module attribute', () => {
    const { container } = render(
      <GovukRadios name="example" options={options} />
    )
    const root = container.querySelector('.govuk-radios') as HTMLElement
    expect(root).not.toBeNull()
    expect(root.hasAttribute('data-module')).toBe(false)
  })

  it('renders each option with canonical markup and indexed auto-derived ids', () => {
    const { container } = render(
      <GovukRadios name="example" options={options} />
    )
    const items = container.querySelectorAll('.govuk-radios__item')
    expect(items).toHaveLength(3)

    const inputs = container.querySelectorAll(
      'input.govuk-radios__input'
    ) as NodeListOf<HTMLInputElement>
    expect(inputs).toHaveLength(3)
    expect(inputs[0].getAttribute('id')).toBe('example')
    expect(inputs[1].getAttribute('id')).toBe('example-2')
    expect(inputs[2].getAttribute('id')).toBe('example-3')
    expect(inputs[0].getAttribute('name')).toBe('example')
    expect(inputs[1].getAttribute('name')).toBe('example')
    expect(inputs[2].getAttribute('name')).toBe('example')
    expect(inputs[0].getAttribute('type')).toBe('radio')
    expect(inputs[1].getAttribute('type')).toBe('radio')
    expect(inputs[2].getAttribute('type')).toBe('radio')

    const labels = container.querySelectorAll(
      'label.govuk-label.govuk-radios__label'
    ) as NodeListOf<HTMLLabelElement>
    expect(labels[0].getAttribute('for')).toBe('example')
    expect(labels[1].getAttribute('for')).toBe('example-2')
    expect(labels[2].getAttribute('for')).toBe('example-3')
    expect(labels[0].textContent).toBe('England')
    expect(labels[1].textContent).toBe('Scotland')
    expect(labels[2].textContent).toBe('Wales')
  })

  it('renders hint text when provided in an option and wires aria-describedby', () => {
    const optionsWithHint = [
      { label: 'Yes', value: 'yes', hint: 'Choose yes if it applies' },
      { label: 'No', value: 'no' },
    ]
    const { container } = render(
      <GovukRadios name="example" options={optionsWithHint} />
    )
    const hint = container.querySelector(
      '.govuk-hint.govuk-radios__hint'
    ) as HTMLElement
    expect(hint).not.toBeNull()
    expect(hint.textContent).toBe('Choose yes if it applies')
    expect(hint.id).toBe('example-hint')

    const firstInput = container.querySelector(
      'input.govuk-radios__input'
    ) as HTMLInputElement
    expect(firstInput.getAttribute('aria-describedby')).toBe('example-hint')
  })

  it('controlled: value="scotland" checks the correct input', () => {
    const { container } = render(
      <GovukRadios name="example" options={options} value="scotland" />
    )
    const inputs = container.querySelectorAll(
      'input.govuk-radios__input'
    ) as NodeListOf<HTMLInputElement>
    expect(inputs[0].checked).toBe(false)
    expect(inputs[1].checked).toBe(true)
    expect(inputs[2].checked).toBe(false)
  })

  it('onChange fires with the selected value when an option is clicked', async () => {
    const onChange = vi.fn()

    function Wrapper() {
      const [value, setValue] = useState<string | undefined>(undefined)
      return (
        <GovukRadios
          name="example"
          options={options}
          value={value}
          onChange={(next) => {
            onChange(next)
            setValue(next)
          }}
        />
      )
    }

    render(<Wrapper />)
    await userEvent.click(screen.getByLabelText('Scotland'))
    expect(onChange).toHaveBeenLastCalledWith('scotland')
    expect(
      (screen.getByLabelText('Scotland') as HTMLInputElement).checked
    ).toBe(true)
  })

  it('disabled prop disables all rendered option inputs', () => {
    const { container } = render(
      <GovukRadios name="example" options={options} disabled />
    )
    const inputs = container.querySelectorAll(
      'input.govuk-radios__input'
    ) as NodeListOf<HTMLInputElement>
    inputs.forEach((input) => expect(input.disabled).toBe(true))
  })

  it('composes className without clobbering the canonical govuk-radios class', () => {
    const { container } = render(
      <GovukRadios name="example" options={options} className="mt-2" />
    )
    expect(container.querySelector('.govuk-radios')).toHaveClass('mt-2')
  })

  it('integrates with react-hook-form via <Controller>', async () => {
    const onSubmit = vi.fn()
    type Form = { choice: 'yes' | 'no' | undefined }

    const yesNoOptions = [
      { label: 'Yes', value: 'yes' },
      { label: 'No', value: 'no' },
    ]

    function Wrapper() {
      const { control, handleSubmit } = useForm<Form>({
        defaultValues: { choice: undefined },
      })
      return (
        <form onSubmit={handleSubmit(onSubmit)}>
          <Controller
            control={control}
            name="choice"
            render={({ field: { value, onChange, ref, disabled } }) => (
              <GovukRadios
                name="choice"
                options={yesNoOptions}
                value={value}
                onChange={(next) => onChange(next)}
                disabled={disabled}
                ref={ref}
              />
            )}
          />
          <button type="submit">Submit</button>
        </form>
      )
    }

    render(<Wrapper />)
    await userEvent.click(screen.getByLabelText('Yes'))
    await userEvent.click(screen.getByRole('button', { name: 'Submit' }))
    expect(onSubmit).toHaveBeenCalledTimes(1)
    expect(onSubmit.mock.calls[0][0]).toEqual({ choice: 'yes' })
  })

  it('regression — Controller initialised at undefined then setValue("yes") rehydrates', async () => {
    type Form = { choice: 'yes' | 'no' | undefined }

    const yesNoOptions = [
      { label: 'Yes', value: 'yes' },
      { label: 'No', value: 'no' },
    ]

    function Wrapper() {
      const { control, setValue } = useForm<Form>({
        defaultValues: { choice: undefined },
      })

      useEffect(() => {
        const timer = setTimeout(() => setValue('choice', 'yes'), 0)
        return () => clearTimeout(timer)
      }, [setValue])

      return (
        <Controller
          control={control}
          name="choice"
          render={({ field: { value, onChange } }) => (
            <GovukRadios
              name="choice"
              options={yesNoOptions}
              value={value}
              onChange={(next) => onChange(next)}
            />
          )}
        />
      )
    }

    render(<Wrapper />)
    const yes = screen.getByLabelText('Yes') as HTMLInputElement
    const no = screen.getByLabelText('No') as HTMLInputElement
    expect(yes.checked).toBe(false)
    expect(no.checked).toBe(false)

    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 5))
    })
    expect((screen.getByLabelText('Yes') as HTMLInputElement).checked).toBe(
      true
    )
  })
})
