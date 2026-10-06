import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useQuery } from '@tanstack/react-query'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { MicRecorderForm } from '@/components/audio/mic-recorder'
import { TabRecorderForm } from '@/components/audio/tab-recorder/tab-recorder'
import { saveMicrophonePreferences } from '@/lib/microphone-preferences'

vi.mock('@tanstack/react-query', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@tanstack/react-query')>()),
  useQuery: vi.fn(),
}))
vi.mock('@/hooks/use-start-transcription', async () => {
  const { useForm } = await import('react-hook-form')
  return {
    useStartTranscription: () => ({
      form: useForm({ defaultValues: { file: null } }),
      onSubmit: vi.fn(),
    }),
  }
})
vi.mock('@/providers/transcription-db-provider', () => ({
  useRecordingDb: () => ({ addRecording: vi.fn(), updateRecording: vi.fn() }),
}))
vi.mock('@/hooks/use-wake-lock', () => ({
  useWakeLock: () => ({ requestWakeLock: vi.fn(), releaseWakeLock: vi.fn() }),
}))
vi.mock('@/hooks/use-tab-close-warning', () => ({
  useTabCloseWarning: vi.fn(),
}))
vi.mock('@/hooks/use-countdown', () => ({
  useCountdown: () => ({
    isStartingRecording: false,
    isPreparingRecording: false,
    startCountdown: vi.fn(),
    handleLoadingComplete: vi.fn(),
    handleLoadingCancel: vi.fn(),
  }),
}))
vi.mock('@/components/audio/microphone-permission', () => ({
  MicrophonePermission: ({
    onPermissionGranted,
  }: {
    onPermissionGranted: (
      devices: { deviceId: string; label: string }[]
    ) => void
  }) => (
    <button
      type="button"
      onClick={() =>
        onPermissionGranted([
          { deviceId: 'default', label: 'Default microphone' },
          { deviceId: 'teams', label: 'Teams microphone' },
        ])
      }
    >
      Grant permission
    </button>
  ),
}))

describe('recording microphone defaults', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.mocked(useQuery).mockReturnValue({
      data: { id: 'user-1' },
    } as ReturnType<typeof useQuery>)
  })

  it.each([
    { name: 'in-person', Recorder: MicRecorderForm, expected: 'teams' },
    { name: 'online', Recorder: TabRecorderForm, expected: 'default' },
  ])(
    'uses the saved $name default and allows a per-recording override',
    async ({ Recorder, expected }) => {
      saveMicrophonePreferences('user-1', {
        inPerson: 'teams',
        online: 'default',
      })
      render(<Recorder />)
      await userEvent.click(
        screen.getByRole('button', { name: 'Grant permission' })
      )
      const select = screen.getByLabelText('Choose microphone')
      expect(select).toHaveValue(expected)
      const override = expected === 'teams' ? 'default' : 'teams'
      await userEvent.selectOptions(select, override)
      expect(select).toHaveValue(override)
    }
  )

  it.each([MicRecorderForm, TabRecorderForm])(
    'explains fallback instead of using a stale device',
    async (Recorder) => {
      saveMicrophonePreferences('user-1', {
        inPerson: 'missing',
        online: 'missing',
      })
      render(<Recorder />)
      await userEvent.click(
        screen.getByRole('button', { name: 'Grant permission' })
      )
      expect(screen.getByLabelText('Choose microphone')).toHaveValue('default')
      expect(
        screen.getByText(/Your saved microphone is unavailable/)
      ).toBeInTheDocument()
    }
  )
  it.each([MicRecorderForm, TabRecorderForm])(
    'waits for the account after device discovery and then applies the saved default',
    async (Recorder) => {
      saveMicrophonePreferences('user-1', {
        inPerson: 'teams',
        online: 'teams',
      })
      vi.mocked(useQuery).mockReturnValue({
        data: undefined,
        isPending: true,
      } as ReturnType<typeof useQuery>)
      const { rerender } = render(<Recorder />)
      await userEvent.click(
        screen.getByRole('button', { name: 'Grant permission' })
      )
      expect(screen.getByRole('status')).toHaveTextContent(
        'Loading microphone settings...'
      )
      expect(
        screen.queryByLabelText('Choose microphone')
      ).not.toBeInTheDocument()
      expect(
        screen.queryByRole('button', { name: 'Start recording' })
      ).not.toBeInTheDocument()
      vi.mocked(useQuery).mockReturnValue({
        data: { id: 'user-1' },
        isPending: false,
      } as ReturnType<typeof useQuery>)
      rerender(<Recorder />)
      expect(screen.getByLabelText('Choose microphone')).toHaveValue('teams')
      await userEvent.selectOptions(
        screen.getByLabelText('Choose microphone'),
        'default'
      )
      rerender(<Recorder />)
      expect(screen.getByLabelText('Choose microphone')).toHaveValue('default')
    }
  )

  it.each([MicRecorderForm, TabRecorderForm])(
    'uses a visible fallback if account loading fails after discovery',
    async (Recorder) => {
      vi.mocked(useQuery).mockReturnValue({
        data: undefined,
        isPending: true,
      } as ReturnType<typeof useQuery>)
      const { rerender } = render(<Recorder />)
      await userEvent.click(
        screen.getByRole('button', { name: 'Grant permission' })
      )
      vi.mocked(useQuery).mockReturnValue({
        data: undefined,
        isPending: false,
        isError: true,
      } as ReturnType<typeof useQuery>)
      rerender(<Recorder />)
      expect(screen.getByLabelText('Choose microphone')).toHaveValue('default')
      expect(
        screen.getByText(/Your microphone settings could not be loaded/)
      ).toBeInTheDocument()
      vi.mocked(useQuery).mockReturnValue({
        data: { id: 'user-1' },
        isPending: false,
      } as ReturnType<typeof useQuery>)
      saveMicrophonePreferences('user-1', {
        inPerson: 'teams',
        online: 'teams',
      })
      await userEvent.selectOptions(
        screen.getByLabelText('Choose microphone'),
        'default'
      )
      rerender(<Recorder />)
      expect(screen.getByLabelText('Choose microphone')).toHaveValue('default')
    }
  )
})
