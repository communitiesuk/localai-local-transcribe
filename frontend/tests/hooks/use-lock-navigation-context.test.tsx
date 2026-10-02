/* eslint-disable @typescript-eslint/no-explicit-any */
import { act, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import {
  LockNavigationProvider,
  useLockNavigation,
  useLockNavigationContext,
} from '@/hooks/use-lock-navigation-context'

describe('<LockNavigationProvider />', () => {
  beforeEach(() => {
    Object.defineProperty(window, 'navigation', {
      value: new EventTarget(),
      configurable: true,
    })
  })

  afterEach(() => {
    delete (window as any).navigation
  })

  const renderProvider = () =>
    renderHook(() => useLockNavigationContext(), {
      wrapper: LockNavigationProvider,
    })

  const fireBeforeUnload = () => {
    const event = new Event('beforeunload', { cancelable: true })
    window.dispatchEvent(event)
    return event.defaultPrevented
  }

  const fireBrowserBack = (url: string) => {
    const event = Object.assign(new Event('navigate', { cancelable: true }), {
      navigationType: 'traverse',
      destination: { url: `http://localhost${url}` },
    })
    window.navigation.dispatchEvent(event)
    return event.defaultPrevented
  }

  it('does not block leaving the site or going back when navigation is not locked', () => {
    renderProvider()

    expect(fireBeforeUnload()).toBe(false)
    expect(fireBrowserBack('/templates')).toBe(false)
  })

  it.each([true, 'You have unsaved changes'])(
    'blocks leaving the site but not going back when navigation is locked with %s',
    (lock) => {
      const { result } = renderProvider()

      act(() => result.current.setLockNavigation(lock))

      expect(fireBeforeUnload()).toBe(true)
      expect(fireBrowserBack('/templates')).toBe(false)
    }
  )

  it('blocks going back and calls the lock with the destination when navigation is locked with a function', () => {
    const lock = vi.fn()
    const { result } = renderProvider()

    act(() => result.current.setLockNavigation(() => lock))

    expect(fireBrowserBack('/templates?page=2')).toBe(true)
    expect(lock).toHaveBeenCalledWith('/templates?page=2')
  })

  it('stops blocking leaving the site once navigation is unlocked', () => {
    const { result } = renderProvider()

    act(() => result.current.setLockNavigation(true))
    act(() => result.current.setLockNavigation(false))

    expect(fireBeforeUnload()).toBe(false)
  })

  describe('useLockNavigation', () => {
    const renderUseLockNavigation = (
      initialLock: Parameters<typeof useLockNavigation>[0]
    ) =>
      renderHook(
        ({ lock }) => {
          useLockNavigation(lock)
          return useLockNavigationContext()
        },
        { wrapper: LockNavigationProvider, initialProps: { lock: initialLock } }
      )

    it('locks navigation and blocks leaving the site while the lock is set', () => {
      const { result } = renderUseLockNavigation('You have unsaved changes')

      expect(result.current.lockNavigation).toBe('You have unsaved changes')
      expect(fireBeforeUnload()).toBe(true)
    })

    it('updates the lock when it changes', () => {
      const { result, rerender } = renderUseLockNavigation('First message')

      rerender({ lock: 'Second message' })

      expect(result.current.lockNavigation).toBe('Second message')
    })

    it('unlocks navigation once the lock is no longer set', () => {
      const { result, rerender } = renderUseLockNavigation(true)

      rerender({ lock: false })

      expect(result.current.lockNavigation).toBe(false)
      expect(fireBeforeUnload()).toBe(false)
    })

    it('unlocks navigation when the component using it unmounts', () => {
      const { unmount } = renderUseLockNavigation(true)

      unmount()

      expect(fireBeforeUnload()).toBe(false)
    })

    it('calls a function lock with the destination when going back in the browser', () => {
      const lock = vi.fn()
      const { result } = renderUseLockNavigation(lock)

      expect(result.current.lockNavigation).toBe(lock)
      expect(fireBrowserBack('/templates')).toBe(true)
      expect(lock).toHaveBeenCalledWith('/templates')
    })
  })
})
