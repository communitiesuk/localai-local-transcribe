import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useMutation } from '@tanstack/react-query'
import { AiEditPopover } from '@/app/transcriptions/[transcriptionId]/MinuteTab/minute-editor/ai-edit-popover'

vi.mock('@/lib/client/@tanstack/react-query.gen', () => ({
  createMinuteVersionMinutesMinuteIdVersionsPostMutation: () => ({
    mutationKey: ['create-minute-version'],
  }),
}))

vi.mock('@tanstack/react-query', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@tanstack/react-query')>()
  return {
    ...actual,
    useMutation: vi.fn(),
  }
})

const mutateMock = vi.fn()
const resetMock = vi.fn()

const renderPopover = (
  props: Partial<React.ComponentProps<typeof AiEditPopover>> = {}
) =>
  render(
    <AiEditPopover
      disabled={false}
      minuteId="minute-1"
      minuteVersionId="version-1"
      onSuccess={vi.fn()}
      {...props}
    />
  )

beforeEach(() => {
  vi.clearAllMocks()
  vi.mocked(useMutation).mockReturnValue({
    mutate: mutateMock,
    isPending: false,
    isError: false,
    reset: resetMock,
  } as unknown as ReturnType<typeof useMutation>)
})

describe('<AiEditPopover />', () => {
  it('renders the AI Edit trigger button, disabled when instructed', () => {
    renderPopover({ disabled: true })
    expect(screen.getByRole('button', { name: 'AI Edit' })).toBeDisabled()
  })

  it('opens the modal on click and shows the instruction form', () => {
    renderPopover()
    fireEvent.click(screen.getByRole('button', { name: 'AI Edit' }))

    expect(screen.getByRole('heading', { name: 'AI edit' })).toBeInTheDocument()
    expect(
      screen.getByText(
        "Describe what changes you'd like to make to your document"
      )
    ).toBeInTheDocument()
    expect(document.getElementById('ai-edit-instruction')).toBeInTheDocument()
  })

  it('disables Apply Edit until an instruction has been entered', () => {
    renderPopover()
    fireEvent.click(screen.getByRole('button', { name: 'AI Edit' }))

    const applyButton = screen.getByRole('button', { name: 'Apply Edit' })
    expect(applyButton).toBeDisabled()

    fireEvent.change(document.getElementById('ai-edit-instruction')!, {
      target: { value: 'Local transcribe is great' },
    })
    expect(applyButton).toBeEnabled()
  })

  it('calls onEditStart then submits the edit with the current version as source_id', async () => {
    const onEditStart = vi.fn()
    const onSuccess = vi.fn()
    renderPopover({ onEditStart, onSuccess })

    fireEvent.click(screen.getByRole('button', { name: 'AI Edit' }))
    fireEvent.change(document.getElementById('ai-edit-instruction')!, {
      target: { value: 'Make it more formal' },
    })
    fireEvent.submit(
      document.getElementById('ai-edit-instruction')!.closest('form')!
    )

    await waitFor(() => expect(mutateMock).toHaveBeenCalled())

    expect(onEditStart).toHaveBeenCalledOnce()
    expect(mutateMock).toHaveBeenCalledWith(
      {
        path: { minute_id: 'minute-1' },
        body: {
          content_source: 'ai_edit',
          ai_edit_instructions: {
            instruction: 'Make it more formal',
            source_id: 'version-1',
          },
        },
      },
      { onSuccess }
    )
  })

  it('closes the modal when Cancel is clicked and resets any error state', () => {
    renderPopover()
    fireEvent.click(screen.getByRole('button', { name: 'AI Edit' }))
    expect(screen.getByRole('heading', { name: 'AI edit' })).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))

    expect(resetMock).toHaveBeenCalled()
    expect(
      screen.queryByRole('heading', { name: 'AI edit' })
    ).not.toBeInTheDocument()
  })

  it('shows an error banner and preserves the instruction when the request fails', () => {
    vi.mocked(useMutation).mockReturnValue({
      mutate: mutateMock,
      isPending: false,
      isError: true,
      reset: resetMock,
    } as unknown as ReturnType<typeof useMutation>)

    renderPopover()
    fireEvent.click(screen.getByRole('button', { name: 'AI Edit' }))
    fireEvent.change(document.getElementById('ai-edit-instruction')!, {
      target: { value: 'Make it more formal' },
    })

    expect(screen.getByText('There is a problem')).toBeInTheDocument()
    expect(
      screen.getByText(
        'Something went wrong starting your AI edit. Please try again.'
      )
    ).toBeInTheDocument()
    expect(screen.getByDisplayValue('Make it more formal')).toBeInTheDocument()
  })

  it('disables Apply Edit while the request is pending', () => {
    vi.mocked(useMutation).mockReturnValue({
      mutate: mutateMock,
      isPending: true,
      isError: false,
      reset: resetMock,
    } as unknown as ReturnType<typeof useMutation>)

    renderPopover()
    fireEvent.click(screen.getByRole('button', { name: 'AI Edit' }))
    fireEvent.change(document.getElementById('ai-edit-instruction')!, {
      target: { value: 'Make it more formal' },
    })

    expect(screen.getByRole('button', { name: 'Apply Edit' })).toBeDisabled()
  })

  it('resets the error state when the modal is reopened', () => {
    renderPopover()
    fireEvent.click(screen.getByRole('button', { name: 'AI Edit' }))
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))
    resetMock.mockClear()

    fireEvent.click(screen.getByRole('button', { name: 'AI Edit' }))
    expect(resetMock).toHaveBeenCalled()
  })
})
