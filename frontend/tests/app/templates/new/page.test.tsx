/* eslint-disable @typescript-eslint/no-explicit-any */
import { act, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useQuery } from '@tanstack/react-query'
import { ReactNode, startTransition, useEffect, useState } from 'react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import NewTemplatePage from '@/app/templates/new/page'
import DiscardTemplatePage from '@/app/templates/new/discard/page'
import { ServiceNav } from '@/components/layout/service-nav'
import { LockNavigationProvider } from '@/hooks/use-lock-navigation-context'
import { useTemplateCreateStore } from '@/stores/use-template-create-store'

const NEW_PATH = '/templates/new'
const DISCARD_PATH = '/templates/new/discard'

let history: string[] = []
let setRenderedPath: (path: string) => void = () => {}
const currentPath = () => history[history.length - 1]
const navigate = (next: string[]) => {
  history = next
  startTransition(() => setRenderedPath(currentPath()))
}

const mockPush = vi.fn((href: string) => navigate([...history, href]))
const mockBack = vi.fn(() => navigate(history.slice(0, -1)))
const mockRouter = { push: mockPush, back: mockBack }

vi.mock('next/navigation', () => ({
  useRouter: () => mockRouter,
  usePathname: () => currentPath().split('?')[0],
  useSearchParams: () => new URLSearchParams(currentPath().split('?')[1]),
}))

vi.mock('next/link', () => ({
  default: ({
    href,
    onClick,
    children,
    ...props
  }: {
    href: string
    onClick?: (e: React.MouseEvent<HTMLAnchorElement>) => void
    children: ReactNode
  }) => (
    <a
      href={href}
      {...props}
      onClick={(e) => {
        onClick?.(e)
        if (e.defaultPrevented) return
        e.preventDefault()
        mockPush(href)
      }}
    >
      {children}
    </a>
  ),
}))

vi.mock('@/lib/client/@tanstack/react-query.gen', () => ({
  getUserUsersMeGetOptions: vi.fn(() => ({ queryKey: ['current-user'] })),
}))

vi.mock('@tanstack/react-query', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@tanstack/react-query')>()
  return { ...actual, useQuery: vi.fn() }
})

const TestApp = () => {
  const [path, setPath] = useState(currentPath)
  const pathname = path.split('?')[0]

  useEffect(() => {
    setRenderedPath = setPath
  }, [])

  return (
    <LockNavigationProvider>
      <ServiceNav />
      {pathname === NEW_PATH && <NewTemplatePage />}
      {pathname === DISCARD_PATH && <DiscardTemplatePage />}
    </LockNavigationProvider>
  )
}

describe('<NewTemplatePage /> navigation lock', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    history = [NEW_PATH]
    useTemplateCreateStore.setState({ draft: null })
    Object.defineProperty(window, 'navigation', {
      value: new EventTarget(),
      configurable: true,
    })

    vi.mocked(useQuery).mockImplementation(
      () => ({ data: { roles: ['standard_user'] } }) as any
    )
  })

  afterEach(() => {
    delete (window as any).navigation
  })

  const renderPage = async () => {
    await act(async () => render(<TestApp />))
  }

  const editTitle = async (user: ReturnType<typeof userEvent.setup>) => {
    await user.type(screen.getByLabelText('Title'), 'Board minutes')
  }

  const clickAndNavigate = async (
    user: ReturnType<typeof userEvent.setup>,
    text: string
  ) => {
    await act(async () => user.click(screen.getByText(text)))
  }

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
    act(() => {
      window.navigation.dispatchEvent(event)
    })
    return event.defaultPrevented
  }

  it('navigates straight to the destination when there are no unsaved changes', async () => {
    const user = userEvent.setup()
    await renderPage()

    await clickAndNavigate(user, 'Templates')

    expect(mockPush).toHaveBeenLastCalledWith('/templates')
  })

  it('navigates to the discard page when there are unsaved changes', async () => {
    const user = userEvent.setup()
    await renderPage()

    await editTitle(user)
    await clickAndNavigate(user, 'Templates')

    expect(mockPush).toHaveBeenLastCalledWith(
      `${DISCARD_PATH}?destination=%2Ftemplates`
    )
    expect(useTemplateCreateStore.getState().draft).toEqual(
      expect.objectContaining({ name: 'Board minutes' })
    )
  })

  it('includes the clicked navigation item as the destination query param', async () => {
    const user = userEvent.setup()
    await renderPage()

    await editTitle(user)
    await clickAndNavigate(user, 'Settings')

    expect(mockPush).toHaveBeenLastCalledWith(
      `${DISCARD_PATH}?destination=%2Fsettings`
    )
  })

  it('navigates to the discard page without a destination when cancelling', async () => {
    const user = userEvent.setup()
    await renderPage()

    await editTitle(user)
    await clickAndNavigate(user, 'Cancel')

    expect(mockPush).toHaveBeenLastCalledWith(DISCARD_PATH)
  })

  it('navigates straight to the destination once changes have been undone', async () => {
    const user = userEvent.setup()
    await renderPage()

    await editTitle(user)
    await user.clear(screen.getByLabelText('Title'))
    await clickAndNavigate(user, 'Templates')

    expect(mockPush).toHaveBeenLastCalledWith('/templates')
  })

  it('unlocks navigation once on the discard page', async () => {
    const user = userEvent.setup()
    await renderPage()

    await editTitle(user)
    await clickAndNavigate(user, 'Templates')

    expect(
      screen.getByRole('heading', {
        name: 'Are you sure you want to discard this template?',
      })
    ).toBeInTheDocument()

    await clickAndNavigate(user, 'Templates')

    expect(mockPush).toHaveBeenLastCalledWith('/templates')
  })

  it('restores your unsaved changes when you return to the template', async () => {
    const user = userEvent.setup()
    await renderPage()

    await editTitle(user)
    await clickAndNavigate(user, 'Templates')
    await clickAndNavigate(user, 'Cancel')

    expect(mockBack).toHaveBeenCalled()
    expect(screen.getByLabelText('Title')).toHaveValue('Board minutes')
  })

  it('does not warn before leaving the site when there are no unsaved changes', async () => {
    await renderPage()

    expect(fireBeforeUnload()).toBe(false)
  })

  it('warns before leaving the site when there are unsaved changes', async () => {
    const user = userEvent.setup()
    await renderPage()

    await editTitle(user)

    expect(fireBeforeUnload()).toBe(true)
  })

  it('does not warn before leaving the site once changes have been undone', async () => {
    const user = userEvent.setup()
    await renderPage()

    await editTitle(user)
    await user.clear(screen.getByLabelText('Title'))

    expect(fireBeforeUnload()).toBe(false)
  })

  it('does not warn before leaving the site once on the discard page', async () => {
    const user = userEvent.setup()
    await renderPage()

    await editTitle(user)
    await clickAndNavigate(user, 'Templates')

    expect(fireBeforeUnload()).toBe(false)
  })

  it('goes back in the browser normally when there are no unsaved changes', async () => {
    await renderPage()

    expect(fireBrowserBack('/templates')).toBe(false)
    expect(mockPush).not.toHaveBeenCalled()
  })

  it('navigates to the discard page when going back in the browser with unsaved changes', async () => {
    const user = userEvent.setup()
    await renderPage()

    await editTitle(user)

    expect(fireBrowserBack('/templates')).toBe(true)
    expect(mockPush).toHaveBeenLastCalledWith(
      `${DISCARD_PATH}?destination=%2Ftemplates`
    )
  })

  it('goes back in the browser normally once on the discard page', async () => {
    const user = userEvent.setup()
    await renderPage()

    await editTitle(user)
    await clickAndNavigate(user, 'Templates')

    expect(fireBrowserBack(NEW_PATH)).toBe(false)
  })

  const discardWithDestination = async (destination?: string) => {
    history = [
      NEW_PATH,
      destination
        ? `${DISCARD_PATH}?destination=${encodeURIComponent(destination)}`
        : DISCARD_PATH,
    ]
    const user = userEvent.setup()
    await renderPage()
    await clickAndNavigate(user, 'Discard')
  }

  it('goes to the destination after discarding the template', async () => {
    await discardWithDestination('/settings?tab=profile')

    expect(mockPush).toHaveBeenLastCalledWith('/settings?tab=profile')
  })

  it('goes to the templates page after discarding the template when there is no destination', async () => {
    await discardWithDestination()

    expect(mockPush).toHaveBeenLastCalledWith('/templates')
  })

  it('clears the draft after discarding the template', async () => {
    useTemplateCreateStore.setState({
      draft: { name: 'Board minutes' } as any,
    })

    await discardWithDestination()

    expect(useTemplateCreateStore.getState().draft).toBeNull()
  })

  it('goes to the templates page instead of an external destination after discarding the template', async () => {
    await discardWithDestination('//evil.example')

    expect(mockPush).toHaveBeenLastCalledWith('/templates')
  })
})
