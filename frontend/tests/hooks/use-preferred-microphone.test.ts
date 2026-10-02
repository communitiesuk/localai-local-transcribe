import { renderHook } from '@testing-library/react'
import { useQuery } from '@tanstack/react-query'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { usePreferredMicrophone } from '@/hooks/use-preferred-microphone'
import { saveMicrophonePreferences } from '@/lib/microphone-preferences'

vi.mock('@tanstack/react-query', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@tanstack/react-query')>()),
  useQuery: vi.fn(),
}))
const devices = [
  { deviceId: 'default', label: 'Default' },
  { deviceId: 'teams', label: 'Teams' },
]

describe('usePreferredMicrophone', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.mocked(useQuery).mockReturnValue({
      data: { id: 'user-1' },
    } as ReturnType<typeof useQuery>)
  })

  it('resolves the saved default independently for each recording context', () => {
    saveMicrophonePreferences('user-1', {
      inPerson: 'teams',
      online: 'default',
    })
    const inPerson = renderHook(() => usePreferredMicrophone('inPerson'))
    const online = renderHook(() => usePreferredMicrophone('online'))
    expect(inPerson.result.current(devices)).toEqual({
      deviceId: 'teams',
      warning: null,
    })
    expect(online.result.current(devices)).toEqual({
      deviceId: 'default',
      warning: null,
    })
  })

  it('isolates users and chooses the browser default without a preference', () => {
    saveMicrophonePreferences('user-2', { inPerson: 'teams', online: 'teams' })
    const { result } = renderHook(() => usePreferredMicrophone('online'))
    expect(result.current(devices)).toEqual({
      deviceId: 'default',
      warning: null,
    })
  })

  it('falls back with a visible warning for stale device IDs', () => {
    saveMicrophonePreferences('user-1', { inPerson: 'missing', online: '' })
    const { result } = renderHook(() => usePreferredMicrophone('inPerson'))
    expect(result.current(devices).deviceId).toBe('default')
    expect(result.current(devices).warning).toMatch(
      /saved microphone is unavailable/
    )
  })

  it('reports unreadable preferences and falls back safely', () => {
    localStorage.setItem('local-transcribe:microphones:v1:user-1', '{}')
    const { result } = renderHook(() => usePreferredMicrophone('online'))
    expect(result.current(devices).deviceId).toBe('default')
    expect(result.current(devices).warning).toMatch(
      /settings could not be loaded/
    )
  })

  it('warns when account settings are not available yet', () => {
    vi.mocked(useQuery).mockReturnValue({ data: undefined } as ReturnType<
      typeof useQuery
    >)
    const { result } = renderHook(() => usePreferredMicrophone('online'))
    expect(result.current(devices).deviceId).toBe('default')
    expect(result.current(devices).warning).toMatch(
      /settings could not be loaded/
    )
  })
})
