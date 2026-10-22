import { render, waitFor } from '@testing-library/react'
import { useEffect, useState } from 'react'
import { afterEach, describe, expect, it } from 'vitest'
import { useFocusHashTarget } from '@/hooks/use-focus-hash-target'

const Page = () => {
  useFocusHashTarget()

  return (
    <>
      <input id="first-field" />
      <input id="second-field" />
    </>
  )
}

const LoadingPage = () => {
  const [ready, setReady] = useState(false)

  useFocusHashTarget(ready)

  useEffect(() => {
    setReady(true)
  }, [])

  return ready ? <input id="second-field" /> : <p>Loading</p>
}

const setHash = (hash: string) => {
  window.location.hash = hash
}

describe('useFocusHashTarget', () => {
  afterEach(() => {
    setHash('')
  })

  it('focuses the field named in the url fragment', () => {
    setHash('#second-field')

    render(<Page />)

    expect(document.activeElement).toBe(document.getElementById('second-field'))
  })

  it('focuses the field once it has rendered, not while the page is loading', async () => {
    setHash('#second-field')

    render(<LoadingPage />)

    await waitFor(() =>
      expect(document.activeElement).toBe(
        document.getElementById('second-field')
      )
    )
  })

  it('leaves focus alone when there is no fragment', () => {
    render(<Page />)

    expect(document.activeElement).toBe(document.body)
  })

  it('leaves focus alone when the fragment names nothing on the page', () => {
    setHash('#not-here')

    render(<Page />)

    expect(document.activeElement).toBe(document.body)
  })
})
