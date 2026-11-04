import { render } from '@testing-library/react'
import { useRef } from 'react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { useNativeCopyTracking } from '@/hooks/use-native-copy-tracking'
import { copyHTML } from '@/lib/utils'

const onCopyMock = vi.fn()

const Summary = () => {
  const containerRef = useRef<HTMLDivElement>(null)

  useNativeCopyTracking({ containerRef, onCopy: onCopyMock })

  return (
    <>
      <div ref={containerRef}>
        <p data-testid="summary-text">Summary body</p>
      </div>
      <p data-testid="outside-text">Transcript body</p>
    </>
  )
}

/** Puts a real selection across the given element's text, as a user drag would. */
const selectTextIn = (element: Element) => {
  const range = document.createRange()
  range.selectNodeContents(element)
  const selection = window.getSelection()!
  selection.removeAllRanges()
  selection.addRange(range)
}

const collapseSelection = () => {
  const selection = window.getSelection()!
  selection.removeAllRanges()
}

const pressCopy = () => {
  document.dispatchEvent(new Event('copy', { bubbles: true }))
}

describe('useNativeCopyTracking', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.useFakeTimers({ shouldAdvanceTime: true })
  })

  afterEach(() => {
    vi.useRealTimers()
    collapseSelection()
  })

  it('records a copy of a selection inside the container', () => {
    const { getByTestId } = render(<Summary />)

    selectTextIn(getByTestId('summary-text'))
    pressCopy()

    expect(onCopyMock).toHaveBeenCalledTimes(1)
  })

  it('ignores a copy of a selection outside the container', () => {
    const { getByTestId } = render(<Summary />)

    selectTextIn(getByTestId('outside-text'))
    pressCopy()

    expect(onCopyMock).not.toHaveBeenCalled()
  })

  it('ignores a copy with an empty selection', () => {
    render(<Summary />)

    collapseSelection()
    pressCopy()

    expect(onCopyMock).not.toHaveBeenCalled()
  })

  it('throttles a burst from a held-down Ctrl+C to one event', () => {
    const { getByTestId } = render(<Summary />)
    selectTextIn(getByTestId('summary-text'))

    pressCopy()
    pressCopy()
    pressCopy()

    expect(onCopyMock).toHaveBeenCalledTimes(1)
  })

  it('records a deliberate second copy once the throttle window has passed', () => {
    const { getByTestId } = render(<Summary />)
    selectTextIn(getByTestId('summary-text'))

    pressCopy()
    vi.advanceTimersByTime(2001)
    pressCopy()

    expect(onCopyMock).toHaveBeenCalledTimes(2)
  })

  it('stops listening once unmounted', () => {
    const { getByTestId, unmount } = render(<Summary />)
    selectTextIn(getByTestId('summary-text'))

    unmount()
    pressCopy()

    expect(onCopyMock).not.toHaveBeenCalled()
  })

  // Pins the assumption behind copy_type: the Copy button and native copies are disjoint, so a
  // button copy is never also counted as a native one. A refactor of copyHTML to
  // document.execCommand('copy') would fire a real copy event and start double counting.
  it('is not triggered by the Copy button writing to the clipboard', async () => {
    const write = vi.fn().mockResolvedValue(undefined)
    vi.stubGlobal('navigator', {
      ...navigator,
      clipboard: { write, writeText: vi.fn().mockResolvedValue(undefined) },
    })
    vi.stubGlobal(
      'ClipboardItem',
      class {
        constructor(public items: Record<string, Blob>) {}
      }
    )

    const { getByTestId } = render(<Summary />)
    selectTextIn(getByTestId('summary-text'))

    await copyHTML('<p>Summary body</p>')

    expect(write).toHaveBeenCalled()
    expect(onCopyMock).not.toHaveBeenCalled()

    vi.unstubAllGlobals()
  })
})
