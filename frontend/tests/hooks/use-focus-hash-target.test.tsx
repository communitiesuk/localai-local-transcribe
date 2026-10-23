import { render } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import { useFocusHashTarget } from '@/hooks/use-focus-hash-target'

const Page = ({ ready = true }: { ready?: boolean }) => {
  useFocusHashTarget(ready)

  if (!ready) {
    return <p>Loading</p>
  }

  return (
    <>
      <input id="first-field" />
      <input id="second-field" />
    </>
  )
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

  it('focuses the field once it has rendered, not while the page is loading', () => {
    setHash('#second-field')

    const { rerender } = render(<Page ready={false} />)
    rerender(<Page />)

    expect(document.activeElement).toBe(document.getElementById('second-field'))
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
