/* eslint-disable @typescript-eslint/no-explicit-any */
import { act, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import {
  LockNavigationProvider,
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
})
