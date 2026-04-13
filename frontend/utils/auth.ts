export interface UserAuthorisationResult {
  email: string
  isAuthorised: boolean
  authReason: string
}

type AuthResponse = {
  decision: {
    is_authorised: boolean
    auth_reason: string
  }
  metadata: {
    user_email: string
  }
}

// Validate required environment variables
// Don't expect an AUTH_API_URL if you're running dev locally / running frontend tests
const authApiUrl =
  process.env.AUTH_API_URL ||
  (process.env.NODE_ENV === 'development' ? 'development' : undefined)

if (!authApiUrl) {
  throw new Error('AUTH_API_URL is not defined in the environment variables.')
}

process.env.AUTH_API_URL = authApiUrl

export async function parseAuthToken(
  token: string
): Promise<UserAuthorisationResult | null> {
  if (!token) {
    console.error('No auth token provided to parse')
    return null
  }

  try {
    const res = await fetch(`${authApiUrl}/tokens/authorise`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ app_name: process.env.REPO || 'unknown', token }),
      signal: AbortSignal.timeout(5000),
    })

    const data = (await res.json()) as AuthResponse

    const email = data.metadata.user_email

    if (!email) {
      console.error('No email found in user info')
      return null
    }

    return {
      email,
      isAuthorised: data.decision.is_authorised,
      authReason: data.decision.auth_reason,
    }
  } catch (error) {
    console.error('Error parsing auth token:', error)
    return null
  }
}
