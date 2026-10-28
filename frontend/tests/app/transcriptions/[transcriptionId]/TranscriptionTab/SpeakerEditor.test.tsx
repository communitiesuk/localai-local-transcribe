import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { useFormContext, useWatch } from 'react-hook-form'
import { SpeakerEditor } from '@/app/transcriptions/[transcriptionId]/TranscriptionTab/SpeakerEditor'
import type { DialogueEntry } from '@/lib/client'

vi.mock('react-hook-form', () => ({
  useFormContext: vi.fn(),
  useWatch: vi.fn(),
}))

const setBannerMock = vi.fn()
vi.mock('@/stores/use-banner-store', () => ({
  useBannerStore: () => ({ setBanner: setBannerMock }),
}))

global.Audio = vi.fn().mockImplementation(() => ({
  pause: vi.fn(),
  play: vi.fn().mockResolvedValue(undefined),
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
  currentTime: 0,
  paused: true,
})) as unknown as typeof Audio

const mockEntries: DialogueEntry[] = [
  { speaker: 'Alice', text: 'Hello', start_time: 0, end_time: 1 },
  { speaker: 'Bob', text: 'Hi', start_time: 1, end_time: 2 },
]

function setup(onSaveSpeaker = vi.fn().mockResolvedValue(undefined)) {
  vi.mocked(useFormContext).mockReturnValue({ control: {} } as ReturnType<
    typeof useFormContext
  >)
  vi.mocked(useWatch).mockReturnValue(mockEntries)
  render(<SpeakerEditor onSaveSpeaker={onSaveSpeaker} />)
  const openModal = () =>
    fireEvent.click(screen.getByRole('button', { name: 'Edit speaker names' }))
  return { onSaveSpeaker, openModal }
}

describe('<SpeakerEditor />', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('opens the modal when the trigger is clicked', () => {
    const { openModal } = setup()
    openModal()
    expect(screen.getByRole('dialog')).toBeInTheDocument()
  })

  it('displays all speaker names in the list view', () => {
    const { openModal } = setup()
    openModal()
    expect(screen.getByText('Alice')).toBeInTheDocument()
    expect(screen.getByText('Bob')).toBeInTheDocument()
  })

  it('Done is disabled until a name edit is made', () => {
    const { openModal } = setup()
    openModal()
    expect(screen.getByRole('button', { name: 'Done' })).toBeDisabled()
  })

  it('Cancel on list view with no pending changes closes the modal', () => {
    const { openModal } = setup()
    openModal()
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('Cancel on list view with pending changes shows the confirm-discard view', () => {
    const { openModal } = setup()
    openModal()
    fireEvent.click(screen.getAllByRole('button', { name: 'Edit' })[0])
    fireEvent.change(screen.getByRole('textbox'), {
      target: { value: 'Alicia' },
    })
    fireEvent.click(
      screen.getByRole('button', { name: 'Update all occurrences' })
    )
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))
    expect(
      screen.getByRole('heading', { name: 'Discard changes?' })
    ).toBeInTheDocument()
  })

  it('"Cancel" on the interstitial returns to list view with pending changes intact', () => {
    const { openModal } = setup()
    openModal()
    fireEvent.click(screen.getAllByRole('button', { name: 'Edit' })[0])
    fireEvent.change(screen.getByRole('textbox'), {
      target: { value: 'Alicia' },
    })
    fireEvent.click(
      screen.getByRole('button', { name: 'Update all occurrences' })
    )
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))
    expect(screen.getByText('Alicia')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Done' })).toBeEnabled()
  })

  it('"Discard changes" on the interstitial closes the modal', () => {
    const { openModal } = setup()
    openModal()
    fireEvent.click(screen.getAllByRole('button', { name: 'Edit' })[0])
    fireEvent.change(screen.getByRole('textbox'), {
      target: { value: 'Alicia' },
    })
    fireEvent.click(
      screen.getByRole('button', { name: 'Update all occurrences' })
    )
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))
    fireEvent.click(screen.getByRole('button', { name: 'Discard changes' }))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('clicking Edit opens edit view with correct speaker name and title', () => {
    const { openModal } = setup()
    openModal()
    fireEvent.click(screen.getAllByRole('button', { name: 'Edit' })[0])
    expect(screen.getByRole('textbox')).toHaveValue('Alice')
    expect(
      screen.getByRole('heading', { name: 'Edit Alice' })
    ).toBeInTheDocument()
  })

  it('Update is disabled when the value is unchanged', () => {
    const { openModal } = setup()
    openModal()
    fireEvent.click(screen.getAllByRole('button', { name: 'Edit' })[0])
    expect(
      screen.getByRole('button', { name: 'Update all occurrences' })
    ).toBeDisabled()
  })

  it('Update saves the pending name and returns to the list view', () => {
    const { openModal } = setup()
    openModal()
    fireEvent.click(screen.getAllByRole('button', { name: 'Edit' })[0])
    fireEvent.change(screen.getByRole('textbox'), {
      target: { value: 'Alicia' },
    })
    fireEvent.click(
      screen.getByRole('button', { name: 'Update all occurrences' })
    )
    expect(screen.getByText('Alicia')).toBeInTheDocument()
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Done' })).toBeEnabled()
  })

  it('Done is re-disabled when a pending edit is reverted to the original name', () => {
    const { openModal } = setup()
    openModal()
    fireEvent.click(screen.getAllByRole('button', { name: 'Edit' })[0])
    fireEvent.change(screen.getByRole('textbox'), {
      target: { value: 'Alicia' },
    })
    fireEvent.click(
      screen.getByRole('button', { name: 'Update all occurrences' })
    )
    fireEvent.click(screen.getAllByRole('button', { name: 'Edit' })[0])
    fireEvent.change(screen.getByRole('textbox'), {
      target: { value: 'Alice' },
    })
    fireEvent.click(
      screen.getByRole('button', { name: 'Update all occurrences' })
    )
    expect(screen.getByRole('button', { name: 'Done' })).toBeDisabled()
  })

  it('re-editing a speaker shows the pending name, not the original', () => {
    const { openModal } = setup()
    openModal()
    fireEvent.click(screen.getAllByRole('button', { name: 'Edit' })[0])
    fireEvent.change(screen.getByRole('textbox'), {
      target: { value: 'Alicia' },
    })
    fireEvent.click(
      screen.getByRole('button', { name: 'Update all occurrences' })
    )
    fireEvent.click(screen.getAllByRole('button', { name: 'Edit' })[0])
    expect(screen.getByRole('textbox')).toHaveValue('Alicia')
    expect(
      screen.getByRole('heading', { name: 'Edit Alicia' })
    ).toBeInTheDocument()
  })

  it('Cancel with no changes on edit view returns to list', () => {
    const { openModal } = setup()
    openModal()
    fireEvent.click(screen.getAllByRole('button', { name: 'Edit' })[0])
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument()
    expect(
      screen.getByRole('heading', { name: 'Edit speaker names' })
    ).toBeInTheDocument()
  })

  it('Cancel with unsaved changes returns to list without saving', () => {
    const { openModal } = setup()
    openModal()
    fireEvent.click(screen.getAllByRole('button', { name: 'Edit' })[0])
    fireEvent.change(screen.getByRole('textbox'), {
      target: { value: 'Alicia' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument()
    expect(
      screen.getByRole('heading', { name: 'Edit speaker names' })
    ).toBeInTheDocument()
    expect(screen.getByText('Alice')).toBeInTheDocument()
  })

  it('the trigger button is disabled when disabled prop is true', () => {
    vi.mocked(useFormContext).mockReturnValue({ control: {} } as ReturnType<
      typeof useFormContext
    >)
    vi.mocked(useWatch).mockReturnValue(mockEntries)
    render(<SpeakerEditor onSaveSpeaker={vi.fn()} disabled={true} />)
    expect(
      screen.getByRole('button', { name: 'Edit speaker names' })
    ).toBeDisabled()
  })

  it('Done calls onSaveSpeaker for each pending change and shows a success banner', async () => {
    const { openModal, onSaveSpeaker } = setup()
    openModal()
    fireEvent.click(screen.getAllByRole('button', { name: 'Edit' })[0])
    fireEvent.change(screen.getByRole('textbox'), {
      target: { value: 'Alicia' },
    })
    fireEvent.click(
      screen.getByRole('button', { name: 'Update all occurrences' })
    )
    fireEvent.click(screen.getByRole('button', { name: 'Done' }))
    await waitFor(() => {
      expect(onSaveSpeaker).toHaveBeenCalledWith('Alice', 'Alicia')
      expect(setBannerMock).toHaveBeenCalledWith(
        expect.objectContaining({
          message: 'Speaker names updated',
          variant: 'success',
        })
      )
    })
  })
})
