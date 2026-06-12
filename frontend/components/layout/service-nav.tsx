'use client'

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
import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { useLockNavigationContext } from '@/hooks/use-lock-navigation-context'

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
      pathname === '/' || pathname === '/new' || pathname.startsWith('/new/'),
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
    name: 'User management',
    href: '/user-management',
    isActive: (pathname: string) =>
      pathname === '/user-management' ||
      pathname.startsWith('/user-management/'),
    isAdminOnly: true,
  },
]

export function ServiceNav() {
  const pathname = usePathname()
  const router = useRouter()
  const { lockNavigation, setLockNavigation } = useLockNavigationContext()
  const { data: user } = useQuery(getUserUsersMeGetOptions())

  const hasAdminRole = hasAnyRole(user?.roles, [
    UserRole.LOCAL_AUTHORITY_ADMIN,
    UserRole.MHCLG_SUPPORT_ADMIN,
  ])

  const visibleItems = navItems.filter(
    (item) => !item.isAdminOnly || hasAdminRole
  )

  return (
    <section
      className="govuk-service-navigation"
      data-module="govuk-service-navigation"
      aria-label="Service information"
    >
      <div className="govuk-width-container">
        <div className="govuk-service-navigation__container">
          <span className="govuk-service-navigation__service-name">
            <Link href="/" className="govuk-service-navigation__link">
              Local Transcribe
            </Link>
          </span>
          <nav aria-label="Menu" className="govuk-service-navigation__wrapper">
            <button
              type="button"
              className="govuk-service-navigation__toggle govuk-js-service-navigation-toggle"
              aria-controls="navigation"
              hidden
              aria-hidden="true"
            >
              Menu
            </button>
            <ul className="govuk-service-navigation__list" id="navigation">
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
                    {lockNavigation ? (
                      <AlertDialog>
                        <AlertDialogTrigger asChild>
                          <button
                            type="button"
                            className="govuk-service-navigation__link"
                            aria-current={active ? 'page' : undefined}
                            style={{
                              background: 'none',
                              border: 'none',
                              padding: 0,
                              font: 'inherit',
                              cursor: 'pointer',
                              textAlign: 'left',
                            }}
                          >
                            {linkContent}
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
                                router.push(item.href)
                              }}
                            >
                              Continue
                            </AlertDialogAction>
                          </AlertDialogFooter>
                        </AlertDialogContent>
                      </AlertDialog>
                    ) : (
                      <Link
                        href={item.href}
                        className="govuk-service-navigation__link"
                        aria-current={active ? 'page' : undefined}
                      >
                        {linkContent}
                      </Link>
                    )}
                  </li>
                )
              })}
            </ul>
          </nav>
        </div>
      </div>
    </section>
  )
}
