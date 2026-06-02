import { Header } from '@/components/layout/header'
import { API_PROXY_PATH } from '@/lib/constants'
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

describe('<Header />', () => {
  it('renders the canonical govuk-template__header > govuk-header structure', () => {
    const { container } = render(<Header />)
    const outer = container.querySelector('header.govuk-template__header')
    expect(outer).not.toBeNull()
    expect(outer?.querySelector('.govuk-header')).not.toBeNull()
  })

  it('wraps content in govuk-header__container + govuk-width-container', () => {
    const { container } = render(<Header />)
    const wrap = container.querySelector('.govuk-header__container')
    expect(wrap).toHaveClass('govuk-width-container')
  })

  it('renders the MHCLG logo + Local Transcribe product name linking to /', () => {
    render(<Header />)
    const home = screen.getByRole('link', { name: /Local Transcribe/ })
    expect(home).toHaveAttribute('href', '/')
    expect(home).toHaveClass('govuk-header__homepage-link')
    expect(screen.getByText('Local Transcribe')).toHaveClass(
      'govuk-header__product-name'
    )
  })

  it('renders Sign out as an inverse link pointing at the proxy signout endpoint', () => {
    render(<Header />)
    const nav = screen.getByRole('navigation', { name: 'Account' })
    expect(nav).toBeInTheDocument()
    const link = screen.getByRole('link', { name: 'Sign out' })
    expect(link).toHaveClass('govuk-link', 'govuk-link--inverse')
    expect(link).toHaveAttribute('href', `${API_PROXY_PATH}/signout`)
  })
})
