export type UserAuthorisationResult = {
  email: string
  isAuthorised: boolean
  authReason: string
}

function decodeJwtPayload(token: string): Record<string, unknown> | null {
  try {
    const payload = token.split('.')[1]
    const decoded = Buffer.from(payload, 'base64url').toString('utf8')
    return JSON.parse(decoded)
  } catch {
    return null
  }
}

export async function parseAuthToken(
  token: string
): Promise<UserAuthorisationResult | null> {
  if (!token) {
    console.error('No auth token provided to parse')
    return null
  }

  try {
    const payload = decodeJwtPayload(token)

    if (!payload) {
      console.error('Failed to decode JWT payload')
      return null
    }

    const email = payload.email as string | undefined
    if (!email) {
      console.error('No email found in JWT payload')
      return null
    }

    return { email, isAuthorised: true, authReason: 'OIDC' }
  } catch (error) {
    console.error('Error parsing auth token:', error)
    return null
  }
}
