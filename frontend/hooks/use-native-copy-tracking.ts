'use client'

import { useEffect, useRef, type RefObject } from 'react'

/**
 * A burst of `copy` events — from holding Ctrl/Cmd+C — is one intent, not many. Throttled here
 * rather than deduplicated in the report, so the stored rows need no cleaning.
 */
const COPY_THROTTLE_MS = 2000

/**
 * Records Ctrl/Cmd+C and context-menu copies made from inside `containerRef`.
 *
 * Deliberately listens on `document` rather than on the container: a selection that starts inside
 * the container and ends outside it fires `copy` on the common ancestor, which a container-only
 * listener would miss. Containment is then checked against the selection instead.
 *
 * This does not double count our own Copy button. `copyHTML` writes via `navigator.clipboard`,
 * a programmatic write that raises no `copy` event, so the `button` and `native` paths are
 * disjoint. A refactor to `document.execCommand('copy')` would break that — see the test that
 * pins it.
 *
 * Treat the resulting figure as a lower bound: screenshots, drag-and-drop, extension copies and
 * copies made out of the downloaded `.docx` are all invisible here.
 */
export function useNativeCopyTracking({
  containerRef,
  onCopy,
}: {
  containerRef: RefObject<HTMLElement | null>
  onCopy: () => void
}) {
  const lastCopyAtRef = useRef(0)
  // Held in a ref so an inline onCopy does not rebind the listener on every render.
  const onCopyRef = useRef(onCopy)

  useEffect(() => {
    onCopyRef.current = onCopy
  }, [onCopy])

  useEffect(() => {
    const handleCopy = () => {
      const container = containerRef.current
      if (!container) {
        return
      }

      const selection = window.getSelection()
      if (!selection) {
        return
      }

      // `copy` still fires on a collapsed selection, which puts nothing on the clipboard.
      if (!selection.toString().trim()) {
        return
      }

      // anchorNode is where the selection began. A text node is fine here: Node.contains
      // matches text nodes as well as elements.
      if (!selection.anchorNode || !container.contains(selection.anchorNode)) {
        return
      }

      const now = Date.now()
      if (now - lastCopyAtRef.current < COPY_THROTTLE_MS) {
        return
      }
      lastCopyAtRef.current = now

      onCopyRef.current()
    }

    document.addEventListener('copy', handleCopy)
    return () => document.removeEventListener('copy', handleCopy)
  }, [containerRef])
}
