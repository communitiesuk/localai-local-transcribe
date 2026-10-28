import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { MicrophoneSettings } from '@/components/settings/microphone-settings'
import {
  loadMicrophonePreferences,
  saveMicrophonePreferences,
} from '@/lib/microphone-preferences'

const devices = [
  { deviceId: 'default', kind: 'audioinput', label: 'Default microphone' },
  { deviceId: 'teams', kind: 'audioinput', label: 'Teams microphone' },
  { deviceId: 'speaker', kind: 'audiooutput', label: 'Speaker' },
]

describe('MicrophoneSettings', () => {
  const enumerateDevices = vi.fn()
  const getUserMedia = vi.fn()
  const onSuccess = vi.fn()
  beforeEach(() => {
    vi.restoreAllMocks()
    vi.clearAllMocks()
    localStorage.clear()
    enumerateDevices.mockResolvedValue(devices)
    Object.defineProperty(navigator, 'mediaDevices', {
      configurable: true,
      value: { enumerateDevices, getUserMedia },
    })
  })

  it('loads devices without requesting permission and saves independent defaults', async () => {
    render(<MicrophoneSettings userId="user-1" onSuccess={onSuccess} />)
    const inPerson = await screen.findByLabelText('In person')
    expect(getUserMedia).not.toHaveBeenCalled()
    expect(
      screen.queryByRole('option', { name: 'Speaker' })
    ).not.toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: 'Save microphones' })
    ).toBeDisabled()
    await userEvent.selectOptions(screen.getByLabelText('Online'), 'teams')
    await userEvent.click(
      screen.getByRole('button', { name: 'Save microphones' })
    )
    await waitFor(() =>
      expect(onSuccess).toHaveBeenCalledWith('Microphone settings updated')
    )
    expect(inPerson).toHaveValue('default')
    expect(loadMicrophonePreferences('user-1')).toEqual({
      inPerson: 'default',
      online: 'teams',
    })
    expect(
      screen.getByRole('button', { name: 'Save microphones' })
    ).toBeDisabled()
  })

  it('restores preferences, explains a missing device and allows saving the fallback', async () => {
    saveMicrophonePreferences('user-1', { inPerson: 'gone', online: 'teams' })
    render(<MicrophoneSettings userId="user-1" onSuccess={onSuccess} />)
    expect(await screen.findByLabelText('Online')).toHaveValue('teams')
    expect(screen.getByLabelText('In person')).toHaveValue('default')
    expect(
      screen.getByText(
        'A saved microphone is unavailable. Check and save your selected microphones.'
      )
    ).toBeInTheDocument()
    await userEvent.click(
      screen.getByRole('button', { name: 'Save microphones' })
    )
    await waitFor(() =>
      expect(loadMicrophonePreferences('user-1').inPerson).toBe('default')
    )
  })

  it('requests permission explicitly and stops the temporary stream', async () => {
    enumerateDevices.mockResolvedValueOnce([
      { deviceId: '', kind: 'audioinput', label: '' },
    ])
    const stop = vi.fn()
    getUserMedia.mockResolvedValue({ getTracks: () => [{ stop }] })
    render(<MicrophoneSettings userId="user-1" onSuccess={onSuccess} />)
    await userEvent.click(
      await screen.findByRole('button', { name: 'Allow microphone access' })
    )
    await screen.findByLabelText('In person')
    expect(getUserMedia).toHaveBeenCalledWith({ audio: true })
    expect(stop).toHaveBeenCalledOnce()
  })

  it('shows permission denial and allows retry', async () => {
    enumerateDevices.mockResolvedValue([])
    getUserMedia.mockRejectedValue(
      new DOMException('Denied', 'NotAllowedError')
    )
    render(<MicrophoneSettings userId="user-1" onSuccess={onSuccess} />)
    await userEvent.click(
      await screen.findByRole('button', { name: 'Allow microphone access' })
    )
    expect(
      await screen.findByText(/Microphone permission denied/)
    ).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: 'Allow microphone access' })
    ).toBeEnabled()
    expect(onSuccess).not.toHaveBeenCalledWith('Microphone settings updated')
  })

  it('shows enumeration failures rather than a success state', async () => {
    enumerateDevices.mockRejectedValue(new Error('Unavailable'))
    render(<MicrophoneSettings userId="user-1" onSuccess={onSuccess} />)
    expect(
      await screen.findByText(/Microphone devices could not be loaded/)
    ).toBeInTheDocument()
  })

  it('explains when granting permission still provides no usable devices', async () => {
    enumerateDevices.mockResolvedValue([])
    getUserMedia.mockResolvedValue({ getTracks: () => [{ stop: vi.fn() }] })
    render(<MicrophoneSettings userId="user-1" onSuccess={onSuccess} />)
    await userEvent.click(
      await screen.findByRole('button', { name: 'Allow microphone access' })
    )
    expect(
      await screen.findByText(/No usable microphones were found/)
    ).toBeInTheDocument()
  })

  it('reports a failed device check separately from a storage failure', async () => {
    render(<MicrophoneSettings userId="user-1" onSuccess={onSuccess} />)
    await userEvent.selectOptions(
      await screen.findByLabelText('Online'),
      'teams'
    )
    enumerateDevices.mockRejectedValueOnce(new Error('Device check failed'))
    await userEvent.click(
      screen.getByRole('button', { name: 'Save microphones' })
    )
    expect(
      await screen.findByText(/Microphone devices could not be checked/)
    ).toBeInTheDocument()
    expect(onSuccess).not.toHaveBeenCalledWith('Microphone settings updated')
  })

  it('reports corrupt preferences and permits overwriting them', async () => {
    localStorage.setItem('local-transcribe:microphones:v1:user-1', 'invalid')
    render(<MicrophoneSettings userId="user-1" onSuccess={onSuccess} />)
    await screen.findByLabelText('In person')
    expect(
      screen.getByText(/Your saved microphone settings could not be loaded/)
    ).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: 'Save microphones' })
    ).toBeEnabled()
  })

  it('reports storage failures without claiming success', async () => {
    render(<MicrophoneSettings userId="user-1" onSuccess={onSuccess} />)
    await screen.findByLabelText('Online')
    await userEvent.selectOptions(screen.getByLabelText('Online'), 'teams')
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('Storage blocked')
    })
    await userEvent.click(
      screen.getByRole('button', { name: 'Save microphones' })
    )
    expect(
      await screen.findByText(/Your microphone settings could not be saved/)
    ).toBeInTheDocument()
    expect(onSuccess).not.toHaveBeenCalledWith('Microphone settings updated')
  })

  it('rejects a device disconnected before save', async () => {
    render(<MicrophoneSettings userId="user-1" onSuccess={onSuccess} />)
    await screen.findByLabelText('Online')
    await userEvent.selectOptions(screen.getByLabelText('Online'), 'teams')
    enumerateDevices.mockResolvedValue([devices[0]])
    await userEvent.click(
      screen.getByRole('button', { name: 'Save microphones' })
    )
    expect(
      await screen.findByText(/A selected microphone is no longer available/)
    ).toBeInTheDocument()
    expect(onSuccess).not.toHaveBeenCalledWith('Microphone settings updated')
  })

  it('preserves both unsaved selections and their saved baseline when refreshing', async () => {
    saveMicrophonePreferences('user-1', {
      inPerson: 'default',
      online: 'teams',
    })
    const getItem = vi.spyOn(Storage.prototype, 'getItem')
    render(<MicrophoneSettings userId="user-1" onSuccess={onSuccess} />)
    await userEvent.selectOptions(
      await screen.findByLabelText('In person'),
      'teams'
    )
    await userEvent.selectOptions(screen.getByLabelText('Online'), 'default')
    getItem.mockClear()
    await userEvent.click(
      screen.getByRole('button', { name: 'Refresh microphones' })
    )
    await waitFor(() =>
      expect(
        screen.getByRole('button', { name: 'Refresh microphones' })
      ).toBeEnabled()
    )
    expect(getItem).not.toHaveBeenCalled()
    expect(screen.getByLabelText('In person')).toHaveValue('teams')
    expect(screen.getByLabelText('Online')).toHaveValue('default')
    expect(
      screen.getByRole('button', { name: 'Save microphones' })
    ).toBeEnabled()
    expect(loadMicrophonePreferences('user-1')).toEqual({
      inPerson: 'default',
      online: 'teams',
    })
    await userEvent.click(
      screen.getByRole('button', { name: 'Save microphones' })
    )
    await waitFor(() =>
      expect(
        screen.getByRole('button', { name: 'Save microphones' })
      ).toBeDisabled()
    )
    expect(loadMicrophonePreferences('user-1')).toEqual({
      inPerson: 'teams',
      online: 'default',
    })
  })

  it('falls back only for a disconnected draft device without changing the baseline', async () => {
    const external = {
      deviceId: 'external',
      kind: 'audioinput',
      label: 'External microphone',
    }
    enumerateDevices.mockResolvedValue([...devices, external])
    saveMicrophonePreferences('user-1', { inPerson: 'teams', online: 'teams' })
    render(<MicrophoneSettings userId="user-1" onSuccess={onSuccess} />)
    await userEvent.selectOptions(
      await screen.findByLabelText('In person'),
      'external'
    )
    enumerateDevices.mockResolvedValue(devices)
    await userEvent.click(
      screen.getByRole('button', { name: 'Refresh microphones' })
    )
    await screen.findByText(
      'A selected microphone is unavailable. Check and save your selected microphones.'
    )
    expect(screen.getByLabelText('In person')).toHaveValue('default')
    expect(screen.getByLabelText('Online')).toHaveValue('teams')
    expect(
      screen.getByRole('button', { name: 'Save microphones' })
    ).toBeEnabled()
    expect(loadMicrophonePreferences('user-1')).toEqual({
      inPerson: 'teams',
      online: 'teams',
    })
  })

  it('preserves a draft through a failed refresh and retry', async () => {
    render(<MicrophoneSettings userId="user-1" onSuccess={onSuccess} />)
    await userEvent.selectOptions(
      await screen.findByLabelText('Online'),
      'teams'
    )
    enumerateDevices.mockRejectedValueOnce(new Error('Unavailable'))
    await userEvent.click(
      screen.getByRole('button', { name: 'Refresh microphones' })
    )
    await screen.findByText(/Microphone devices could not be loaded/)
    getUserMedia.mockResolvedValue({ getTracks: () => [{ stop: vi.fn() }] })
    await userEvent.click(
      screen.getByRole('button', { name: 'Allow microphone access' })
    )
    expect(await screen.findByLabelText('Online')).toHaveValue('teams')
    expect(
      screen.getByRole('button', { name: 'Save microphones' })
    ).toBeEnabled()
  })
})
