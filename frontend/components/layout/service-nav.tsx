'use client'

import { ReactNode, useCallback, useEffect, useRef, useState } from 'react'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import { getUserUsersMeGetOptions } from '@/lib/client/@tanstack/react-query.gen'
import { UserRole, hasAnyRole } from '@/lib/utils'
import { useBannerStore } from '@/stores/use-banner-store'
import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { useLockNavigationContext } from '@/hooks/use-lock-navigation-context'
import { cn } from '@/lib/utils'

interface NavItem {
  name: string
  href: string
  isActive: (pathname: string) => boolean
  isAdminOnly?: boolean
}

const navItems: NavItem[] = [
  {
    name: 'Home',
    href: '/',
    isActive: (pathname: string) =>
      pathname === '/' ||
      pathname === '/new' ||
      pathname.startsWith('/new/') ||
      pathname.startsWith('/recordings/'),
  },
  {
    name: 'My recordings',
    href: '/transcriptions',
    isActive: (pathname: string) =>
      pathname === '/transcriptions' || pathname.startsWith('/transcriptions/'),
  },
  {
    name: 'Templates',
    href: '/templates',
    isActive: (pathname: string) =>
      pathname === '/templates' || pathname.startsWith('/templates/'),
  },
  {
    name: 'Settings',
    href: '/settings',
    isActive: (pathname: string) =>
      pathname === '/settings' || pathname.startsWith('/settings/'),
  },
  {
    name: 'Support',
    href: '/support',
    isActive: (pathname: string) =>
      pathname === '/support' || pathname.startsWith('/support/'),
  },
  {
    name: 'User management',
    href: '/user-management',
    isActive: (pathname: string) =>
      pathname === '/user-management' ||
      pathname.startsWith('/user-management/'),
    isAdminOnly: true,
  },
]

interface SafeLinkProps {
  href: string
  children: ReactNode
  ariaCurrent?: 'page'
}

function SafeLink({ href, children, ariaCurrent }: SafeLinkProps) {
  const router = useRouter()
  const { lockNavigation, setLockNavigation } = useLockNavigationContext()
  const clearBanner = useBannerStore((store) => store.clearBanner)

  const handleClick = () => {
    // banner shouldn't persist on page change
    clearBanner()
  }

  if (lockNavigation) {
    return (
      <AlertDialog>
        <AlertDialogTrigger asChild>
          <button
            type="button"
            className="govuk-service-navigation__link"
            aria-current={ariaCurrent}
            style={{
              background: 'none',
              border: 'none',
              padding: 0,
              font: 'inherit',
              cursor: 'pointer',
              textAlign: 'left',
            }}
          >
            {children}
          </button>
        </AlertDialogTrigger>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              Are you sure you want to leave the page?
            </AlertDialogTitle>
            <AlertDialogDescription>
              {typeof lockNavigation === 'string'
                ? lockNavigation
                : `You have a recording that has not been uploaded, are you sure you
              want to leave this page? (Your recording will be discarded if you
              do not upload it, or save a local copy.)`}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                setLockNavigation(false)
                router.push(href)
              }}
            >
              Continue
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    )
  }

  return (
    <Link
      href={href}
      className="govuk-service-navigation__link"
      aria-current={ariaCurrent}
      onClick={handleClick}
    >
      {children}
    </Link>
  )
}

// Sub-pixel tolerance so that a row which fits exactly is not treated as
// overflowing. Deliberately tiny: with 'User management' visible the nav only
// has a few pixels of slack at the maximum page width, so a larger cushion
// would pin admins to the menu at every width.
const OVERFLOW_TOLERANCE_PX = 0.5

// GOV.UK only lays the nav out as a single row from the tablet breakpoint.
// Below it the list is not a flex row and items have no horizontal spacing,
// so measuring there would be meaningless — it is always the menu.
const TABLET_BREAKPOINT = 641

export function ServiceNav() {
  const pathname = usePathname()
  const { data: user } = useQuery(getUserUsersMeGetOptions())
  const [isMobile, setIsMobile] = useState(false)
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const serviceNameRef = useRef<HTMLSpanElement>(null)
  const measureRef = useRef<HTMLUListElement>(null)

  // The visible list collapses in mobile mode, so it cannot tell us when there
  // is room again. The hidden list always renders every item on one row, which
  // gives a stable measurement in both directions.
  const updateIsMobile = useCallback(() => {
    if (window.innerWidth < TABLET_BREAKPOINT) {
      setIsMobile(true)
      return
    }

    const container = containerRef.current
    const serviceName = serviceNameRef.current
    const measure = measureRef.current
    if (!container || !serviceName || !measure) return

    // offsetWidth excludes margins, but the service name has a sizeable right
    // margin that the links cannot encroach on, so add it back.
    const { marginRight } = window.getComputedStyle(serviceName)
    const serviceNameWidth =
      serviceName.getBoundingClientRect().width + (parseFloat(marginRight) || 0)

    const available = container.clientWidth - serviceNameWidth
    if (available <= 0) return

    const required = measure.getBoundingClientRect().width
    const mobile = required - available > OVERFLOW_TOLERANCE_PX
    setIsMobile(mobile)
    if (!mobile) setIsMenuOpen(false)
  }, [])

  const hasAdminRole = hasAnyRole(user?.roles, [
    UserRole.LOCAL_AUTHORITY_ADMIN,
    UserRole.MHCLG_SUPPORT_ADMIN,
  ])

  const visibleItems = navItems.filter(
    (item) => !item.isAdminOnly || hasAdminRole
  )

  // Re-measure when the item set changes: 'User management' appears once the
  // admin role loads, which makes the row wider than it was on first paint.
  useEffect(() => {
    // ResizeObserver reports the initial size on observe(), so no priming call
    // is needed; the fallback path schedules one after first paint instead.
    if (typeof ResizeObserver === 'undefined') {
      const frame = requestAnimationFrame(updateIsMobile)
      window.addEventListener('resize', updateIsMobile)
      return () => {
        cancelAnimationFrame(frame)
        window.removeEventListener('resize', updateIsMobile)
      }
    }

    const observer = new ResizeObserver(updateIsMobile)
    if (containerRef.current) observer.observe(containerRef.current)
    if (measureRef.current) observer.observe(measureRef.current)
    return () => observer.disconnect()
  }, [updateIsMobile, visibleItems.length])

  if (pathname?.startsWith('/terms-of-use')) {
    return null
  }

  return (
    <section
      className="govuk-service-navigation"
      aria-label="Service information"
    >
      <div className="govuk-width-container">
        <div className="govuk-service-navigation__container" ref={containerRef}>
          <span
            className="govuk-service-navigation__service-name"
            ref={serviceNameRef}
          >
            <SafeLink href="/">Local Transcribe</SafeLink>
          </span>
          <nav aria-label="Menu" className="govuk-service-navigation__wrapper">
            <button
              type="button"
              className="govuk-service-navigation__toggle govuk-js-service-navigation-toggle"
              aria-controls="navigation"
              aria-expanded={isMenuOpen}
              hidden={!isMobile}
              onClick={() => setIsMenuOpen((open) => !open)}
            >
              Menu
            </button>
            <ul
              className={cn(
                'govuk-service-navigation__list',
                isMobile && !isMenuOpen
                  ? 'max-h-0 overflow-hidden'
                  : 'max-h-96',
                isMobile && isMenuOpen && 'flex-col'
              )}
              style={{ transition: 'max-height 0.2s ease-in-out' }}
              id="navigation"
              aria-hidden={isMobile && !isMenuOpen}
            >
              {visibleItems.map((item) => {
                const active = item.isActive(pathname)
                const linkContent = active ? (
                  <strong className="govuk-service-navigation__active-fallback">
                    {item.name}
                  </strong>
                ) : (
                  item.name
                )

                return (
                  <li
                    key={item.href}
                    className={[
                      'govuk-service-navigation__item',
                      active ? 'govuk-service-navigation__item--active' : '',
                    ]
                      .filter(Boolean)
                      .join(' ')}
                  >
                    <SafeLink
                      href={item.href}
                      ariaCurrent={active ? 'page' : undefined}
                    >
                      {linkContent}
                    </SafeLink>
                  </li>
                )
              })}
            </ul>
            {/* Mirrors the nav as a single row so we can detect when the real
                links would no longer fit. Hidden from layout and assistive
                technology; only its width is ever read. */}
            <ul
              ref={measureRef}
              aria-hidden="true"
              className="govuk-service-navigation__list"
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                display: 'flex',
                flexWrap: 'nowrap',
                width: 'max-content',
                maxHeight: 'none',
                whiteSpace: 'nowrap',
                visibility: 'hidden',
                pointerEvents: 'none',
              }}
            >
              {visibleItems.map((item) => (
                <li key={item.href} className="govuk-service-navigation__item">
                  <span className="govuk-service-navigation__link">
                    {item.name}
                  </span>
                </li>
              ))}
            </ul>
          </nav>
        </div>
      </div>
    </section>
  )
}
