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
    expect(inPerson.result.current.resolve(devices)).toEqual({
      deviceId: 'teams',
      warning: null,
    })
    expect(online.result.current.resolve(devices)).toEqual({
      deviceId: 'default',
      warning: null,
    })
  })

  it('isolates users and chooses the browser default without a preference', () => {
    saveMicrophonePreferences('user-2', { inPerson: 'teams', online: 'teams' })
    const { result } = renderHook(() => usePreferredMicrophone('online'))
    expect(result.current.resolve(devices)).toEqual({
      deviceId: 'default',
      warning: null,
    })
  })

  it('falls back with a visible warning for stale device IDs', () => {
    saveMicrophonePreferences('user-1', { inPerson: 'missing', online: '' })
    const { result } = renderHook(() => usePreferredMicrophone('inPerson'))
    expect(result.current.resolve(devices).deviceId).toBe('default')
    expect(result.current.resolve(devices).warning).toMatch(
      /saved microphone is unavailable/
    )
  })

  it('reports unreadable preferences and falls back safely', () => {
    localStorage.setItem('local-transcribe:microphones:v1:user-1', '{}')
    const { result } = renderHook(() => usePreferredMicrophone('online'))
    expect(result.current.resolve(devices).deviceId).toBe('default')
    expect(result.current.resolve(devices).warning).toMatch(
      /settings could not be loaded/
    )
  })

  it('warns when account loading has failed', () => {
    vi.mocked(useQuery).mockReturnValue({
      data: undefined,
      isPending: false,
      isError: true,
    } as ReturnType<typeof useQuery>)
    const { result } = renderHook(() => usePreferredMicrophone('online'))
    expect(result.current.isReady).toBe(true)
    expect(result.current.resolve(devices).deviceId).toBe('default')
    expect(result.current.resolve(devices).warning).toMatch(
      /settings could not be loaded/
    )
  })

  it('exposes readiness until the account query settles', () => {
    vi.mocked(useQuery).mockReturnValue({
      data: undefined,
      isPending: true,
    } as ReturnType<typeof useQuery>)
    const { result, rerender } = renderHook(() =>
      usePreferredMicrophone('online')
    )
    expect(result.current.isReady).toBe(false)
    saveMicrophonePreferences('user-1', { inPerson: '', online: 'teams' })
    vi.mocked(useQuery).mockReturnValue({
      data: { id: 'user-1' },
      isPending: false,
    } as ReturnType<typeof useQuery>)
    rerender()
    expect(result.current.isReady).toBe(true)
    expect(result.current.resolve(devices)).toEqual({
      deviceId: 'teams',
      warning: null,
    })
  })
})
