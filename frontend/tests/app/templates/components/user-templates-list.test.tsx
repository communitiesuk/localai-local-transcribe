import { UserTemplatesList } from '@/app/templates/components/user-templates-list'
import { render, screen } from '@testing-library/react'
import { useQuery } from '@tanstack/react-query'
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('@/lib/client/@tanstack/react-query.gen', () => ({
  getTemplatesTemplatesGetOptions: () => ({ queryKey: ['default-templates'] }),
  getUserTemplatesUserTemplatesGetOptions: () => ({ queryKey: ['templates'] }),
}))

vi.mock('@tanstack/react-query', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@tanstack/react-query')>()
  return {
    ...actual,
    useQuery: vi.fn(),
  }
})

const defaultTemplates = [
  {
    name: 'General',
    description: 'Standard default meeting summary',
    category: 'Common',
    agenda_usage: 'optional',
  },
]

const userTemplates = [
  {
    id: 'template-1',
    name: 'Custom assessment',
    description: 'A custom assessment template',
    content: '',
    heading: '',
    updated_datetime: '2025-01-02T00:00:00Z',
    type: 'form',
    questions: null,
  },
]

const configureQueries = () => {
  vi.mocked(useQuery).mockImplementation(((opts: { queryKey?: unknown[] }) => {
    switch (opts?.queryKey?.[0]) {
      case 'default-templates':
        return {
          data: defaultTemplates,
          isLoading: false,
          isError: false,
        }
      case 'templates':
        return {
          data: userTemplates,
          isLoading: false,
          isError: false,
        }
    }
    return undefined
  }) as unknown as typeof useQuery)
}

beforeEach(() => {
  vi.clearAllMocks()
  configureQueries()
})

describe('<UserTemplatesList />', () => {
  it('shows standard and user templates in separate sections', () => {
    render(<UserTemplatesList />)

    expect(
      screen.getByRole('heading', { name: 'Standard templates' })
    ).toBeInTheDocument()
    expect(
      screen.getByRole('heading', { name: 'Your templates' })
    ).toBeInTheDocument()
    expect(screen.getByText('General')).toBeInTheDocument()
    expect(screen.getByText('Custom assessment')).toBeInTheDocument()
    expect(screen.getByText('02/01/2025')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Edit' })).toHaveAttribute(
      'href',
      '/templates/template-1'
    )
  })
})
