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
  '/service-unavailable',
  '/health',
  '/monitoring',
  '/privacy-council-employees',
  '/privacy-members-public',
  '/support',
  '/signout',
  '/assets', // Bypass middleware for static asset files
]

const TOU_PATH = '/terms-of-use'
const SERVICE_UNAVAILABLE_PATH = '/service-unavailable'

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
    let token: string | null = null

    if (process.env.ENVIRONMENT !== 'local') {
      token = req.headers.get('x-amzn-oidc-data')

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
      }
    } else {
      authResult = {
        email: 'test@test.co.uk',
        isAuthorised: true,
        authReason: 'LOCAL_TESTING',
      }
    }

    let backendAuthResponse: Response

    try {
      backendAuthResponse = await fetch(
        `${process.env.BACKEND_HOST}/users/me`,
        {
          headers: token ? { 'x-amzn-oidc-data': token } : undefined,
        }
      )
    } catch (error) {
      console.error('Backend could not be reached:', error)
      return redirectTo(req, SERVICE_UNAVAILABLE_PATH)
    }

    if (backendAuthResponse.status === 401) {
      return redirectTo(req, '/unauthorised')
    }

    if (!backendAuthResponse.ok) {
      console.error(
        `Backend returned ${backendAuthResponse.status} when authorising ${pathname}`
      )
      return redirectTo(req, SERVICE_UNAVAILABLE_PATH)
    }

    let user: { accepted_tou?: boolean } | null = null

    try {
      user = await backendAuthResponse.json()
    } catch (error) {
      console.error('Backend response could not be read:', error)
      return redirectTo(req, SERVICE_UNAVAILABLE_PATH)
    }

    if (!user) {
      console.error(`Backend returned no user when authorising ${pathname}`)
      return redirectTo(req, SERVICE_UNAVAILABLE_PATH)
    }

    if (!user.accepted_tou && !pathname.startsWith(TOU_PATH)) {
      return redirectTo(req, TOU_PATH)
    }

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
  matcher: ['/((?!_next/static|_next/image|favicon.ico|api/health).*)'],
}
