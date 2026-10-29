'use client'

import { useEffect } from 'react'

export function useFocusHashTarget(ready = true) {
  useEffect(() => {
    if (!ready) {
      return
    }

    const fieldId = window.location.hash.slice(1)

    if (fieldId) {
      document.getElementById(fieldId)?.focus()
    }
  }, [ready])
}
