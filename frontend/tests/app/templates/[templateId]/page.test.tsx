/* eslint-disable @typescript-eslint/no-explicit-any */
import { act, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useQuery } from '@tanstack/react-query'
import { ReactNode, startTransition, useEffect, useState } from 'react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import EditTemplatePage from '@/app/templates/[templateId]/page'
import CancelTemplateEditPage from '@/app/templates/[templateId]/cancel/page'
import { ServiceNav } from '@/components/layout/service-nav'
import { LockNavigationProvider } from '@/hooks/use-lock-navigation-context'
import { useTemplateDraftStore } from '@/stores/use-template-draft-store'

const TEMPLATE_ID = 'template-1'
const EDIT_PATH = `/templates/${TEMPLATE_ID}`
const CANCEL_PATH = `/templates/${TEMPLATE_ID}/cancel`

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
  getUserTemplateUserTemplatesTemplateIdGetOptions: vi.fn(() => ({
    queryKey: ['template'],
  })),
  getUserUsersMeGetOptions: vi.fn(() => ({ queryKey: ['current-user'] })),
}))

vi.mock('@tanstack/react-query', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@tanstack/react-query')>()
  return { ...actual, useQuery: vi.fn() }
})

const template = {
  id: TEMPLATE_ID,
  name: 'Board minutes',
  description: 'Monthly board meeting',
  content: '<p>Agenda</p>',
  heading: '',
  questions: null,
  type: 'document',
}

const params = Promise.resolve({ templateId: TEMPLATE_ID })

const TestApp = () => {
  const [path, setPath] = useState(currentPath)
  const pathname = path.split('?')[0]

  useEffect(() => {
    setRenderedPath = setPath
  }, [])

  return (
    <LockNavigationProvider>
      <ServiceNav />
      {pathname === EDIT_PATH && <EditTemplatePage params={params} />}
      {pathname === CANCEL_PATH && <CancelTemplateEditPage params={params} />}
    </LockNavigationProvider>
  )
}

describe('<EditTemplatePage /> navigation lock', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    history = [EDIT_PATH]
    useTemplateDraftStore.setState({ draft: null })
    Object.defineProperty(window, 'navigation', {
      value: new EventTarget(),
      configurable: true,
    })

    vi.mocked(useQuery).mockImplementation(
      (options: any) =>
        ({
          data:
            options.queryKey?.[0] === 'current-user'
              ? { roles: ['standard_user'] }
              : template,
        }) as any
    )
  })

  afterEach(() => {
    delete (window as any).navigation
  })

  const renderPage = async () => {
    await act(async () => render(<TestApp />))
  }

  const editTitle = async (user: ReturnType<typeof userEvent.setup>) => {
    await user.type(screen.getByLabelText('Title'), ' (draft)')
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

  it('navigates to the discard changes page when there are unsaved changes', async () => {
    const user = userEvent.setup()
    await renderPage()

    await editTitle(user)
    await clickAndNavigate(user, 'Templates')

    expect(mockPush).toHaveBeenLastCalledWith(
      `${CANCEL_PATH}?destination=%2Ftemplates`
    )
    expect(useTemplateDraftStore.getState().draft).toEqual({
      templateId: TEMPLATE_ID,
      data: expect.objectContaining({ name: 'Board minutes (draft)' }),
    })
  })

  it('includes the clicked navigation item as the destination query param', async () => {
    const user = userEvent.setup()
    await renderPage()

    await editTitle(user)
    await clickAndNavigate(user, 'Settings')

    expect(mockPush).toHaveBeenLastCalledWith(
      `${CANCEL_PATH}?destination=%2Fsettings`
    )
  })

  it('navigates straight to the destination once changes have been undone', async () => {
    const user = userEvent.setup()
    await renderPage()

    const title = screen.getByLabelText('Title')
    await editTitle(user)
    await user.clear(title)
    await user.type(title, 'Board minutes')
    await clickAndNavigate(user, 'Templates')

    expect(mockPush).toHaveBeenLastCalledWith('/templates')
  })

  it('unlocks navigation once on the discard changes page', async () => {
    const user = userEvent.setup()
    await renderPage()

    await editTitle(user)
    await clickAndNavigate(user, 'Templates')

    expect(
      screen.getByRole('heading', {
        name: 'Are you sure you want to discard your changes?',
      })
    ).toBeInTheDocument()

    await clickAndNavigate(user, 'Templates')

    expect(mockPush).toHaveBeenLastCalledWith('/templates')
  })

  it('keeps your unsaved changes when the template is reloaded', async () => {
    const user = userEvent.setup()
    let rerender!: ReturnType<typeof render>['rerender']
    await act(async () => {
      rerender = render(<TestApp />).rerender
    })

    await editTitle(user)

    const updatedTemplate = { ...template, description: 'Quarterly meeting' }
    const originalUseQuery = vi.mocked(useQuery).getMockImplementation()!
    vi.mocked(useQuery).mockImplementation((options: any) =>
      options.queryKey?.[0] === 'template'
        ? ({ data: updatedTemplate } as any)
        : originalUseQuery(options)
    )
    await act(async () => rerender(<TestApp />))

    expect(screen.getByLabelText('Title')).toHaveValue('Board minutes (draft)')
  })

  it('restores your unsaved changes when you return to the template', async () => {
    const user = userEvent.setup()
    await renderPage()

    await editTitle(user)
    await clickAndNavigate(user, 'Templates')
    await clickAndNavigate(user, 'Cancel')

    expect(mockBack).toHaveBeenCalled()
    expect(screen.getByLabelText('Title')).toHaveValue('Board minutes (draft)')
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

    const title = screen.getByLabelText('Title')
    await editTitle(user)
    await user.clear(title)
    await user.type(title, 'Board minutes')

    expect(fireBeforeUnload()).toBe(false)
  })

  it('does not warn before leaving the site once on the discard changes page', async () => {
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

  it('navigates to the discard changes page when going back in the browser with unsaved changes', async () => {
    const user = userEvent.setup()
    await renderPage()

    await editTitle(user)

    expect(fireBrowserBack('/templates')).toBe(true)
    expect(mockPush).toHaveBeenLastCalledWith(
      `${CANCEL_PATH}?destination=%2Ftemplates`
    )
  })

  it('goes back in the browser normally once on the discard changes page', async () => {
    const user = userEvent.setup()
    await renderPage()

    await editTitle(user)
    await clickAndNavigate(user, 'Templates')

    expect(fireBrowserBack(EDIT_PATH)).toBe(false)
  })
})
