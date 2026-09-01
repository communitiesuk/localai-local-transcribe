import { describe, expect, it, vi, beforeEach } from 'vitest'
import { MinuteVersionSelect } from '@/app/transcriptions/[transcriptionId]/MinuteTab/minute-editor/minute-version-select'
import { render, screen } from '@testing-library/react'
import { MinuteVersionResponse } from '@/lib/client'
import userEvent from '@testing-library/user-event'

const minuteVersions: MinuteVersionResponse[] = [
  {
    id: '3',
    created_datetime: '2024-01-03t00:00:00z',
    minute_id: '1',
    status: 'completed',
    html_content: 'version 3',
    error: null,
    ai_edit_instructions: null,
    content_source: 'ai_edit',
  },
  {
    id: '2',
    created_datetime: '2024-01-02t00:00:00z',
    minute_id: '1',
    status: 'completed',
    html_content: 'version 2',
    error: null,
    ai_edit_instructions: null,
    content_source: 'manual_edit',
  },
  {
    id: '1',
    created_datetime: '2024-01-01t00:00:00z',
    minute_id: '1',
    status: 'completed',
    html_content: 'version 1',
    error: null,
    ai_edit_instructions: null,
    content_source: 'initial_generation',
  },
]

describe('<MinuteVersionSelect />', () => {
  it('renders all versions', () => {
    render(
      <MinuteVersionSelect
        minuteVersions={minuteVersions}
        setVersion={() => null}
      />
    )

    expect(screen.getByText('1. Original (01/01/24 00:00)')).toBeInTheDocument()
    expect(
      screen.getByText('2. Manual edit (02/01/24 00:00)')
    ).toBeInTheDocument()
    expect(screen.getByText('3. AI edit (03/01/24 00:00)')).toBeInTheDocument()
    expect(screen.getAllByRole('option').length).toBe(minuteVersions.length)
  })

  it('renders selected version', () => {
    const selectedVersionId = minuteVersions[1].id
    render(
      <MinuteVersionSelect
        minuteVersions={minuteVersions}
        version={selectedVersionId}
        setVersion={() => null}
      />
    )

    expect(screen.getByRole('combobox')).toHaveValue(selectedVersionId)
  })

  it('calls setVersion on version change', async () => {
    const setVersionMock = vi.fn()

    render(
      <MinuteVersionSelect
        minuteVersions={minuteVersions}
        setVersion={setVersionMock}
      />
    )
    await userEvent.selectOptions(
      screen.getByRole('combobox'),
      screen.getByRole('option', { name: '2. Manual edit (02/01/24 00:00)' })
    )

    expect(setVersionMock).toHaveBeenCalledOnce()
  })
})
