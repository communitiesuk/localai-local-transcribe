import { NextRequest, NextResponse } from 'next/server'
import {
  createAlbJwtVerifier,
  parseAuthToken,
  type UserAuthorisationResult,
} from './utils/auth'
import { API_PROXY_PATH } from './lib/constants'

const verifier =
  process.env.ENVIRONMENT !== 'local' ? createAlbJwtVerifier() : null

// Define paths that should be public (no authorisation required)
const PUBLIC_PATHS = [
  '/unauthorised',
  '/health',
  '/monitoring',
  '/privacy',
  '/support',
  '/signout',
  '/assets', // Bypass middleware for static asset files
]

const TOU_PATH = '/terms-of-use'

export async function proxy(req: NextRequest) {
  try {
    const { pathname } = req.nextUrl

    // Check if the requested path is public
    if (PUBLIC_PATHS.some((path) => pathname.startsWith(path))) {
      return NextResponse.next()
    }

    // Proxy directly to the backend for API requests
    if (pathname.startsWith(API_PROXY_PATH)) {
      const url = new URL(req.url)
      const newPath = `${url.pathname.replace(API_PROXY_PATH, '')}`
      const newUrl = process.env.BACKEND_HOST + newPath + url.search + url.hash
      return NextResponse.rewrite(newUrl, { request: req })
    }

    // Authorise user for frontend access
    let authResult: UserAuthorisationResult | null = null
    let backendAuthResponse: Response | null = null

    if (process.env.ENVIRONMENT !== 'local') {
      const token = req.headers.get('x-amzn-oidc-data')

      if (!token) {
        console.error(
          `No auth token found in headers when accessing ${pathname}`
        )
        return redirectTo(req, '/unauthorised')
      }

      if (verifier) {
        authResult = await parseAuthToken(verifier, token)

        if (authResult?.isAuthorised !== true) {
          console.error(`User is not authorised to access ${pathname}`)
          return redirectTo(req, '/unauthorised')
        }

        console.info(
          `User ${authResult.email} authorisation result: ${authResult.isAuthorised}`
        )
      }
      backendAuthResponse = await fetch(
        `${process.env.BACKEND_HOST}/users/me`,
        {
          headers: { 'x-amzn-oidc-data': token },
        }
      )
    } else {
      authResult = {
        email: 'test@test.co.uk',
        isAuthorised: true,
        authReason: 'LOCAL_TESTING',
      }
      backendAuthResponse = await fetch(`${process.env.BACKEND_HOST}/users/me`)
    }

    if (backendAuthResponse.status === 401) {
      return redirectTo(req, '/unauthorised')
    }

    // TODO(@unassigned): check TOU accepted once AIILG-764 implemented
    // https://mhclgdigital.atlassian.net/browse/AIILG-764
    // const user = await backendAuthResponse.json()
    // if (!user.accepted_tou && !pathname.startsWith(TOU_PATH)) {
    //   return redirectTo(req, TOU_PATH)
    // }

    return NextResponse.next()
  } catch (error) {
    console.error('Error authorising token:', error)
    return redirectTo(req, '/unauthorised')
  }
}

function redirectTo(req: NextRequest, page: string) {
  const url = req.nextUrl.clone()
  url.pathname = page
  return NextResponse.redirect(url)
}

// Configure which paths this middleware should run on
export const config = {
  matcher: [
  '/((?!_next/static|_next/image|favicon.ico|api/health).*)',
  ],
}