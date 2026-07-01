import { GovukTextarea } from '@/components/govuk/textarea'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { createRef } from 'react'
import { Controller, useForm } from 'react-hook-form'
import { describe, expect, it, vi } from 'vitest'

describe('<GovukTextarea />', () => {
  it('renders a textarea with the canonical govuk-textarea class and a default of 5 rows', () => {
    render(<GovukTextarea id="example" />)
    const textarea = screen.getByRole('textbox') as HTMLTextAreaElement
    expect(textarea.tagName).toBe('TEXTAREA')
    expect(textarea).toHaveClass('govuk-textarea')
    expect(textarea).toHaveAttribute('id', 'example')
    expect(textarea).toHaveAttribute('rows', '5')
  })

  it('wires name and a custom rows count through to the rendered element', () => {
    render(<GovukTextarea id="example" name="example" rows={8} />)
    const textarea = screen.getByRole('textbox') as HTMLTextAreaElement
    expect(textarea).toHaveAttribute('name', 'example')
    expect(textarea).toHaveAttribute('rows', '8')
  })

  it('renders the provided value', () => {
    render(<GovukTextarea id="example" value="line one" readOnly />)
    const textarea = screen.getByRole('textbox') as HTMLTextAreaElement
    expect(textarea.value).toBe('line one')
  })

  it('calls onChange with the new value when typed into', async () => {
    const onChange = vi.fn()
    render(<GovukTextarea id="example" onChange={onChange} />)
    const textarea = screen.getByRole('textbox')
    await userEvent.type(textarea, 'a')
    expect(onChange).toHaveBeenCalled()
  })

  it('disabled prop disables the rendered element', () => {
    render(<GovukTextarea id="example" disabled />)
    const textarea = screen.getByRole('textbox')
    expect(textarea).toBeDisabled()
  })

  it('forwards a ref to the underlying textarea element', () => {
    const ref = createRef<HTMLTextAreaElement>()
    render(<GovukTextarea id="example" ref={ref} />)
    expect(ref.current).toBeInstanceOf(HTMLTextAreaElement)
  })

  it('composes a caller-supplied className without clobbering the canonical class', () => {
    render(<GovukTextarea id="example" className="mt-2" />)
    const textarea = screen.getByRole('textbox')
    expect(textarea).toHaveClass('govuk-textarea', 'mt-2')
  })

  it('forwards arbitrary HTML attributes via spread', () => {
    render(<GovukTextarea id="example" aria-describedby="example-hint" />)
    const textarea = screen.getByRole('textbox')
    expect(textarea).toHaveAttribute('aria-describedby', 'example-hint')
  })

  it('integrates with react-hook-form via <Controller>', async () => {
    const onSubmit = vi.fn()
    type Form = { domains: string }

    function Wrapper() {
      const { control, handleSubmit } = useForm<Form>({
        defaultValues: { domains: '' },
      })
      return (
        <form onSubmit={handleSubmit(onSubmit)}>
          <Controller
            control={control}
            name="domains"
            render={({ field: { value, onChange, ref, disabled } }) => (
              <GovukTextarea
                id="domains"
                name="domains"
                value={value}
                onChange={onChange}
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
    await userEvent.type(screen.getByRole('textbox'), 'communities.gov.uk')
    await userEvent.click(screen.getByRole('button', { name: 'Submit' }))
    expect(onSubmit).toHaveBeenCalledTimes(1)
    expect(onSubmit.mock.calls[0][0]).toEqual({
      domains: 'communities.gov.uk',
    })
  })
})
