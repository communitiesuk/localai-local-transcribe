import { render, screen, fireEvent } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { InLineEditForm } from '@/components/govuk/inline-edit-form'

const defaultProps = {
  name: 'Alice',
  onUpdate: vi.fn(),
  onCancel: vi.fn(),
}

describe('<InLineEditForm />', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders an input pre-populated with the name prop', () => {
    render(<InLineEditForm {...defaultProps} />)
    expect(screen.getByRole('textbox')).toHaveValue('Alice')
  })

  it('renders Update and Cancel buttons', () => {
    render(<InLineEditForm {...defaultProps} />)
    expect(screen.getByRole('button', { name: 'Update' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument()
  })

  it('disables Update when value is unchanged', () => {
    render(<InLineEditForm {...defaultProps} />)
    expect(screen.getByRole('button', { name: 'Update' })).toBeDisabled()
  })

  it('enables Update once the value changes', () => {
    render(<InLineEditForm {...defaultProps} />)
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'Bob' } })
    expect(screen.getByRole('button', { name: 'Update' })).toBeEnabled()
  })

  it('calls onUpdate with the current value when Update is clicked', () => {
    render(<InLineEditForm {...defaultProps} />)
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'Bob' } })
    fireEvent.click(screen.getByRole('button', { name: 'Update' }))
    expect(defaultProps.onUpdate).toHaveBeenCalledWith('Bob')
  })

  it('calls onCancel when Cancel is clicked', () => {
    render(<InLineEditForm {...defaultProps} />)
    fireEvent.change(screen.getByRole('textbox'), {
      target: { value: 'Charlie' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))
    expect(defaultProps.onCancel).toHaveBeenCalledOnce()
  })

  it('calls onCancel when Cancel is clicked with no changes', () => {
    render(<InLineEditForm {...defaultProps} />)
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))
    expect(defaultProps.onCancel).toHaveBeenCalledOnce()
  })

  it('re-initialises with a new name when remounted via key change', () => {
    const { rerender } = render(
      <InLineEditForm {...defaultProps} key="Alice" />
    )
    rerender(<InLineEditForm {...defaultProps} name="Bob" key="Bob" />)
    expect(screen.getByRole('textbox')).toHaveValue('Bob')
  })

  it('disables Update when the value is empty or whitespace only', () => {
    render(<InLineEditForm {...defaultProps} />)
    fireEvent.change(screen.getByRole('textbox'), { target: { value: '   ' } })
    expect(screen.getByRole('button', { name: 'Update' })).toBeDisabled()
  })
})
