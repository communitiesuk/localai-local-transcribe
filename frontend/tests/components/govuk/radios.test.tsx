import { GovukRadios } from '@/components/govuk/radios'
import { act, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useEffect, useState } from 'react'
import { Controller, useForm } from 'react-hook-form'
import { describe, expect, it, vi } from 'vitest'

describe('<GovukRadios />', () => {
  it('renders the canonical govuk-radios container with no data-module attribute', () => {
    const { container } = render(
      <GovukRadios name="example">
        <GovukRadios.Item value="yes">Yes</GovukRadios.Item>
        <GovukRadios.Item value="no">No</GovukRadios.Item>
      </GovukRadios>
    )
    const root = container.querySelector('.govuk-radios') as HTMLElement
    expect(root).not.toBeNull()
    expect(root.hasAttribute('data-module')).toBe(false)
  })

  it('renders each item with canonical markup and indexed auto-derived ids', () => {
    const { container } = render(
      <GovukRadios name="example">
        <GovukRadios.Item value="yes">Yes</GovukRadios.Item>
        <GovukRadios.Item value="no">No</GovukRadios.Item>
      </GovukRadios>
    )
    const items = container.querySelectorAll('.govuk-radios__item')
    expect(items).toHaveLength(2)

    const inputs = container.querySelectorAll(
      'input.govuk-radios__input'
    ) as NodeListOf<HTMLInputElement>
    expect(inputs).toHaveLength(2)
    expect(inputs[0].getAttribute('id')).toBe('example')
    expect(inputs[1].getAttribute('id')).toBe('example-2')
    expect(inputs[0].getAttribute('name')).toBe('example')
    expect(inputs[1].getAttribute('name')).toBe('example')
    expect(inputs[0].getAttribute('type')).toBe('radio')
    expect(inputs[1].getAttribute('type')).toBe('radio')

    const labels = container.querySelectorAll(
      'label.govuk-label.govuk-radios__label'
    ) as NodeListOf<HTMLLabelElement>
    expect(labels[0].getAttribute('for')).toBe('example')
    expect(labels[1].getAttribute('for')).toBe('example-2')
  })

  it('renders zero items without crashing or producing inputs', () => {
    const { container } = render(<GovukRadios name="empty">{null}</GovukRadios>)
    const root = container.querySelector('.govuk-radios') as HTMLElement
    expect(root).not.toBeNull()
    expect(container.querySelectorAll('input').length).toBe(0)
  })

  it('controlled: value="yes" checks the first input', () => {
    const { container } = render(
      <GovukRadios name="example" value="yes">
        <GovukRadios.Item value="yes">Yes</GovukRadios.Item>
        <GovukRadios.Item value="no">No</GovukRadios.Item>
      </GovukRadios>
    )
    const inputs = container.querySelectorAll(
      'input.govuk-radios__input'
    ) as NodeListOf<HTMLInputElement>
    expect(inputs[0].checked).toBe(true)
    expect(inputs[1].checked).toBe(false)
  })

  it('onChange fires with the new value on input change (controlled)', async () => {
    const onChange = vi.fn()

    function Wrapper() {
      const [value, setValue] = useState<string | undefined>(undefined)
      return (
        <GovukRadios
          name="example"
          value={value}
          onChange={(next) => {
            onChange(next)
            setValue(next)
          }}
        >
          <GovukRadios.Item value="yes">Yes</GovukRadios.Item>
          <GovukRadios.Item value="no">No</GovukRadios.Item>
        </GovukRadios>
      )
    }

    render(<Wrapper />)
    await userEvent.click(screen.getByLabelText('No'))
    expect(onChange).toHaveBeenLastCalledWith('no')
    expect((screen.getByLabelText('No') as HTMLInputElement).checked).toBe(true)
  })

  it('disabled on parent disables all inputs', () => {
    const { container } = render(
      <GovukRadios name="example" disabled>
        <GovukRadios.Item value="yes">Yes</GovukRadios.Item>
        <GovukRadios.Item value="no">No</GovukRadios.Item>
      </GovukRadios>
    )
    const inputs = container.querySelectorAll(
      'input.govuk-radios__input'
    ) as NodeListOf<HTMLInputElement>
    inputs.forEach((input) => expect(input.disabled).toBe(true))
  })

  it('hint on an item renders canonical govuk-hint markup and wires aria-describedby', () => {
    const { container } = render(
      <GovukRadios name="example">
        <GovukRadios.Item value="yes" hint="Choose yes if it applies">
          Yes
        </GovukRadios.Item>
        <GovukRadios.Item value="no">No</GovukRadios.Item>
      </GovukRadios>
    )
    const hint = container.querySelector(
      '.govuk-hint.govuk-radios__hint'
    ) as HTMLElement
    expect(hint).not.toBeNull()
    expect(hint.id).toBe('example-hint')
    const firstInput = container.querySelector(
      'input.govuk-radios__input'
    ) as HTMLInputElement
    expect(firstInput.getAttribute('aria-describedby')).toBe('example-hint')
  })

  it('composes className without clobbering the canonical govuk-radios class', () => {
    const { container } = render(
      <GovukRadios name="example" className="mt-2">
        <GovukRadios.Item value="yes">Yes</GovukRadios.Item>
      </GovukRadios>
    )
    expect(container.querySelector('.govuk-radios')).toHaveClass('mt-2')
  })

  it('integrates with react-hook-form via <Controller>', async () => {
    const onSubmit = vi.fn()
    type Form = { choice: 'yes' | 'no' | undefined }

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
                value={value}
                onChange={(next) => onChange(next)}
                disabled={disabled}
                ref={ref}
              >
                <GovukRadios.Item value="yes">Yes</GovukRadios.Item>
                <GovukRadios.Item value="no">No</GovukRadios.Item>
              </GovukRadios>
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

    function Wrapper() {
      const { control, setValue } = useForm<Form>({
        defaultValues: { choice: undefined },
      })

      useEffect(() => {
        // Programmatic later-render setValue, mirroring real form flows
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
              value={value}
              onChange={(next) => onChange(next)}
            >
              <GovukRadios.Item value="yes">Yes</GovukRadios.Item>
              <GovukRadios.Item value="no">No</GovukRadios.Item>
            </GovukRadios>
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

describe('<GovukRadios options={[…]} />', () => {
  const options = [
    { label: 'England', value: 'england' },
    { label: 'Scotland', value: 'scotland' },
    { label: 'Wales', value: 'wales' },
  ]

  it('renders all options with canonical markup and auto-derived ids', () => {
    const { container } = render(
      <GovukRadios name="where-do-you-live" options={options} />
    )
    const items = container.querySelectorAll('.govuk-radios__item')
    expect(items).toHaveLength(3)

    const inputs = container.querySelectorAll(
      'input.govuk-radios__input'
    ) as NodeListOf<HTMLInputElement>
    expect(inputs[0].getAttribute('id')).toBe('where-do-you-live')
    expect(inputs[1].getAttribute('id')).toBe('where-do-you-live-2')
    expect(inputs[2].getAttribute('id')).toBe('where-do-you-live-3')
    expect(inputs[0].getAttribute('value')).toBe('england')
    expect(inputs[1].getAttribute('value')).toBe('scotland')
    expect(inputs[2].getAttribute('value')).toBe('wales')

    const labels = container.querySelectorAll(
      'label.govuk-label.govuk-radios__label'
    ) as NodeListOf<HTMLLabelElement>
    expect(labels[0].textContent).toBe('England')
    expect(labels[1].textContent).toBe('Scotland')
    expect(labels[2].textContent).toBe('Wales')
  })

  it('renders hint text when provided in an option', () => {
    const optionsWithHint = [
      { label: 'Yes', value: 'yes', hint: 'Choose this if it applies' },
      { label: 'No', value: 'no' },
    ]
    const { container } = render(
      <GovukRadios name="example" options={optionsWithHint} />
    )
    const hint = container.querySelector(
      '.govuk-hint.govuk-radios__hint'
    ) as HTMLElement
    expect(hint).not.toBeNull()
    expect(hint.textContent).toBe('Choose this if it applies')
    const firstInput = container.querySelector(
      'input.govuk-radios__input'
    ) as HTMLInputElement
    expect(firstInput.getAttribute('aria-describedby')).toBe('example-hint')
  })

  it('controlled: value prop checks the correct option', () => {
    const { container } = render(
      <GovukRadios
        name="where-do-you-live"
        options={options}
        value="scotland"
      />
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
    render(
      <GovukRadios
        name="where-do-you-live"
        options={options}
        onChange={onChange}
      />
    )
    await userEvent.click(screen.getByLabelText('Scotland'))
    expect(onChange).toHaveBeenCalledTimes(1)
    expect(onChange).toHaveBeenCalledWith('scotland')
  })

  it('disabled prop disables all rendered option inputs', () => {
    const { container } = render(
      <GovukRadios name="where-do-you-live" options={options} disabled />
    )
    const inputs = container.querySelectorAll(
      'input.govuk-radios__input'
    ) as NodeListOf<HTMLInputElement>
    inputs.forEach((input) => expect(input.disabled).toBe(true))
  })
})
